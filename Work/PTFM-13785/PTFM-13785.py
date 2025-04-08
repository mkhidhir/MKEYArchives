import warnings
warnings.filterwarnings('ignore')
import requests
import json
import pandas as pd
import time

#A function which calls the Vessel Positions API

def vessel_pos_api(apikey,timespan):
    try:
        url=f' https://services.marinetraffic.com/api/exportvessels/{apikey}?&v=9&timespan={timespan}'
        response_positions = requests.get(url)
        response_positions.raise_for_status()
        if response_positions.ok:
            json_response_positions=response_positions.json()
    except requests.exceptions.HTTPError as e:
        print(f'HTTP error occurred: {e}')
        print(f"Response content: {response_positions.content.decode('utf-8')}")
    return json_response_positions


#a function which creates a dataframeframe to keep specific fields from the output of the vessel_pos_api function

def vessel_positions_output(mt_api_call):

    pos_info=mt_api_call.get('DATA' ,[])
    pos_info_imo= [identifier.get('IMO') for identifier in pos_info]
    pos_info_shipid= [identifier.get('SHIP_ID') for identifier in pos_info]
    pos_info_mmsi= [identifier.get('MMSI') for identifier in pos_info]
    pos_info_timestamp =[timepos.get('TIMESTAMP') for timepos in pos_info]
    pos_info_lat = [lat.get('LAT') for lat in pos_info]
    pos_info_lon = [lon.get('LON') for lon in pos_info]
    pos_info_shipname = [shipname.get('SHIPNAME') for shipname in pos_info]
    pos_info_flag = [flag.get('FLAG') for flag in pos_info]
    pos_info_shiptype = [shiptype.get('SHIPTYPE') for shiptype in pos_info]
    pos_info_lastport = [lastport.get('LAST_PORT') for lastport in pos_info]
    pos_info_nextport = [nextport.get('NEXT_PORT_NAME') for nextport in pos_info]
    pos_info_eta = [eta.get('ETA') for eta in pos_info]
    pos_info_lastporttime = [lastporttime.get('LAST_PORT_TIME') for lastporttime in pos_info]
    vessel_info = {
                        'IMO': pos_info_imo,
                        'SHIP_ID':pos_info_shipid,
                        'MMSI':pos_info_mmsi,
                        'TIMESTAMP':pos_info_timestamp,
                        'LAT':pos_info_lat,
                        'LON':pos_info_lon,
                        'SHIPNAME':pos_info_shipname,
                        'FLAG':pos_info_flag,
                        'SHIPTYPE':pos_info_shiptype,
                        'LAST_PORT': pos_info_lastport,
                        'LAST_PORT_TIME':pos_info_lastporttime,
                        'NEXT_PORT_NAME': pos_info_nextport,
                        'ETA':pos_info_eta
                        }

    df_positions=pd.DataFrame(vessel_info)

    #change the data types
    df_positions['IMO'] = pd.to_numeric(df_positions['IMO'],errors='coerce')
    df_positions['TIMESTAMP']= pd.to_datetime(df_positions['TIMESTAMP'],utc=True)

    return df_positions


#a function which calls the trades api for the vessels fround from the vessel_positions_output function .

def trade_api(headers,mt_output):
    json_response_trade=[]

    for name in mt_output['SHIPNAME']:
        try:
            url_trades=f'https://api.kpler.com/v2/cargo/trades?vessels={name}&size=1&withForecast=False'
            response_trades=requests.get(url_trades,headers=headers)
            response_trades.raise_for_status()
            time.sleep(1)
            if response_trades.ok:
                json_response_trade.append(response_trades.json())
        except requests.exceptions.HTTPError as e:
            print(f'HTTP error occurred: {e}')
            print(f"Response content: {response_trades.content.decode('utf-8')}")
    return json_response_trade


#a function which creates a dataframe to keep specific fields from the output of trade_api function
def trades_output(kp_api_call):

    trade_list = []

    for trade in kp_api_call:
        for vessel in trade:
            trade_data = {
                'IMO': vessel['vessels'][0]['vessel']['imo'],
                'VESSEL_NAME': vessel['vessels'][0]['vessel']['name'],
                'DATE_ORIGIN': vessel['dateOrigin'],
                'DATE_DESTINATION': vessel.get('dateDestination',None),
                'STATUS': vessel['status'],
                'ORIGIN_COUNTRY': vessel['origin']['country'],
                'DESTINATION_COUNTRY': vessel.get('destination', {}).get('country', None),
                'PRODUCT_NAME': vessel['cargo'][0]['product']['name'],
                'QUANTITY_TONS': vessel['cargo'][0]['quantity']['mass']['tons'],
                'VOLUME_BARRELS': vessel['cargo'][0]['quantity']['volume']['barrels'],
                'VOLUME_CUBIC_METERS': vessel['cargo'][0]['quantity']['volume']['cubicMeters'],
                'BUYER': vessel.get('players', {}).get('destinationBuyer', None)
            }
            trade_list.append(trade_data)

    df_trades=pd.DataFrame(trade_list)

    #change the data types
    df_trades['IMO'] = pd.to_numeric(df_trades['IMO'],errors='coerce')
    df_trades['DATE_ORIGIN']=pd.to_datetime(df_trades['DATE_ORIGIN'],utc=False)
    df_trades['DATE_DESTINATION']=pd.to_datetime(df_trades['DATE_DESTINATION'])

    return df_trades

#the last functions combines the output of the vessel_positions_output and trades_output, to create the final table.

def combination_dataset(mt_output,kp_output):
    combined_list=[]

    for i,vessel in mt_output.iterrows():
        for r,trade in kp_output.iterrows():
                #filter based on the IMo and timestamps to match the vessel with her corresponding trade
                if (vessel['IMO']) ==(trade['IMO']) and (vessel['TIMESTAMP']>= trade['DATE_ORIGIN'] and vessel['TIMESTAMP'] <= trade['DATE_DESTINATION']):
                    final_data = {
                        'IMO': vessel['IMO'],
                        'SHIP_ID':vessel['SHIP_ID'],
                        'MMSI':vessel['MMSI'],
                        'TIMESTAMP':vessel['TIMESTAMP'],
                        'LAT':vessel['LAT'],
                        'LON':vessel['LON'],
                        'SHIPNAME':vessel['SHIPNAME'],
                        'FLAG':vessel['FLAG'],
                        'SHIPTYPE':vessel['SHIPTYPE'],
                        'LAST_PORT':vessel['LAST_PORT'] ,
                        'LAST_PORT_TIME':vessel['LAST_PORT_TIME'],
                        'NEXT_PORT_NAME':vessel['NEXT_PORT_NAME'] ,
                        'ETA':vessel['ETA'] ,
                        'PRODUCT_NAME': trade['PRODUCT_NAME'],
                        'QUANTITY_TONS': trade['QUANTITY_TONS'],
                        'VOLUME_BARRELS': trade['VOLUME_BARRELS'],
                        'VOLUME_CUBIC_METERS': trade['VOLUME_CUBIC_METERS'],
                        'BUYER': trade['BUYER']
                    }
                    combined_list.append(final_data)

    df_final=pd.DataFrame(combined_list)
    return df_final


#Call the first function to make the vessel position api request
apikey='API key'
timespan=1440
mt_api_call=vessel_pos_api(apikey,timespan)

#Call the second function to create the vessel position dataframe
mt_output=vessel_positions_output(mt_api_call)

#Call the third function to make the trades api request
headers = {'Authorization': 'Basic API key'}
kp_api_call=trade_api(headers,mt_output)

#Call the forth function  to create the trade dataframe
kp_output=trades_output(kp_api_call)

#Call the final function to combine both dataframes
final=combination_dataset(mt_output,kp_output)

#print the result
print(final)
