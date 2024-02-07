import pandas as pd

def save_xlsx(array, path,header=None):
    df = pd.DataFrame(array)
    df.to_excel(path, index=False,float_format='%.3f')
    df = pd.read_excel(path,dtype=str)
    df.replace(',', '.', inplace=True)
    if header is None : pass
    else:
        df2 = pd.DataFrame([header])
        df = pd.concat([df2, df], ignore_index=True)
    df.to_excel(path, index=False,float_format='%.3f')