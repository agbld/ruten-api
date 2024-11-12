#%%
import requests
import pandas as pd
from tqdm import tqdm
import re
from IPython.display import display

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

BATCH_SIZE = 50 # If you get Error 400, try reducing this number. This means the total number of items might less than this number.

#%%
# Ruten API with DataFrame response. (reverse engineered, might not work as expected)

def api_get_seller_id(seller_nick: str, headers: dict) -> str:
    api_url = f'https://www.ruten.com.tw/store/{seller_nick}/'
    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        # Use regex to find the 'sellerId' in the response text
        match = re.search(r'"sellerId":\s*"(\d+)"', response.text)
        if match:
            return match.group(1)
        else:
            print("Error: sellerId not found in the response.")
            return None
    else:
        print(f"Error: {response.status_code}")
        return None

def api_search_batch(query: str, page_limit: int, page_num: int, offset: int, headers: dict, seller: str = None) -> list:
    query = requests.utils.quote(query)
    if seller:
        api_url = f'https://rtapi.ruten.com.tw/api/search/v3/index.php/core/seller/{seller}/prod?sort=rnk/dc&q={query}&limit={page_limit}&p={page_num}&offset={offset+1}'
    else:
        api_url = f'https://rtapi.ruten.com.tw/api/search/v3/index.php/core/prod?q={query}&type=direct&sort=rnk%2Fdc&limit={page_limit}&p={page_num}&offset={offset+1}'
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json().get('Rows', [])
    else:
        print(f'Error: {response.status_code}')
        return []

def api_list_items_batch(batch_gnos: list, headers: dict) -> list:
    batch_gnos_str = ','.join(batch_gnos)
    api_url = f'https://rapi.ruten.com.tw/api/items/v2/list?gno={batch_gnos_str}&level=simple'
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json().get('data', [])
    else:
        print(f'Error: {response.status_code}')
        return []

#%%
# Dev friendly function

def search(query: str, top_k: int = 10, batch_size: int = BATCH_SIZE, headers: dict = DEFAULT_HEADERS, seller_nick: str = None, verbose: bool = False) -> pd.DataFrame:
    """
    Search for items on Ruten by query and seller's nickname.

    Parameters
    ----------
    query : str
        Search query.
    top_k : int, optional
        Number of items to fetch. Default is 10.
    batch_size : int, optional
        Number of items to fetch in each batch. Default is 50.
    headers : dict, optional
        HTTP headers. Default is DEFAULT_HEADERS.
    seller_nick : str, optional
        Seller's nickname. Search globally if None. Default is None.
    verbose : bool, optional
        Whether to print progress. Default is False.

    Returns
    -------
    pd.DataFrame
        DataFrame of search results.

    Examples
    --------
    ```python
    search('surface pro')
    search('surface pro', top_k=10, seller_nick='xiaokai01', verbose=True)
    ```
    """


    # Get seller ID
    if seller_nick:
        if verbose: print(f'Searching for: {query} by seller: {seller_nick}')
        seller = api_get_seller_id(seller_nick, headers)
        if not seller:
            return pd.DataFrame()
        if verbose: print(f'Seller ID: {seller}')
    else:
        if verbose: print(f'Searching for: {query}')
        seller = None
    
    # Initialize variables
    results = []
    page_num = 1
    offset = 0

    # Fetch search results in batches
    with tqdm(total=top_k, desc='Fetching search results', disable=not verbose) as pbar:
        for _ in range(0, top_k, batch_size):
            data = api_search_batch(query, batch_size, page_num, offset, headers, seller)
            if not data:
                break
            results.extend(data)
            pbar.update(len(data))
            page_num += 1
            offset += batch_size
    df = pd.json_normalize(results).drop_duplicates().head(top_k)

    if verbose: print(f'Found {len(df)} items.')
    
    # Get item IDs
    gnos = df['Id'].tolist()
    if verbose: print(f'Fetching item details for {len(gnos)} items.')
    
    # Fetch item details in batches
    details = []
    for i in tqdm(range(0, len(gnos), batch_size), desc='Fetching item details', disable=not verbose):
        batch_gnos = gnos[i:i + batch_size]
        data = api_list_items_batch(batch_gnos, headers)
        details.extend(data)
    result_df = pd.DataFrame(details)
    if verbose: print(f'Found {len(result_df)} items.')

    return result_df

#%%
# Test

if __name__ == '__main__':
    # Search by specific seller
    test_args = {
        'query': 'Surface Pro',
        'seller_nick': 'xiaokai01',
        'top_k': 100,
    }

    # # Search all items on Ruten
    # test_args = {
    #     'query': 'Surface Pro',
    #     'seller_nick': None,
    #     'top_k': 200,
    # }

    results = search(query=test_args['query'], 
                    top_k=test_args['top_k'], 
                    seller_nick=test_args['seller_nick'],
                    verbose=True)

    # See seller with most items
    sellers = results.groupby('user').size().sort_values(ascending=False).reset_index(name='count')
    
    # Display results and sellers if using Jupyter
    display(results)
    display(sellers)

# %%
