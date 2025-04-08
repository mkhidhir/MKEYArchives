import warnings
warnings.filterwarnings('ignore')
import datetime
from datetime import timedelta
import time
from tkinter import ttk
from tkinter import Tk
import requests
import pandas as pd

class ApiCalls():
    def __init__(self):
        self.filtered_vessels =[]
        self.vessels=[]
        self.df_risk=pd.DataFrame(self.vessels)
    def get_ais_positions(self,url):
        self.filtered_vessels=[]
        try:
            response_positions = requests.get(url)
            response_positions.raise_for_status()

            if response_positions.ok:
                json_response_positions=response_positions.json()

                df_positions = pd.json_normalize(
                    json_response_positions,
                    record_path=['DATA'],
                    sep='_',
                    errors='ignore',
                    )

                distinct_values =df_positions['IMO'].astype(int).unique()
                self.filtered_vessels = distinct_values[distinct_values > 0].tolist()
        except requests.exceptions.HTTPError as e:
            print(f"\nHTTP error occurred: {e}")
            print(f"Response content: {response_positions.content.decode('utf-8')}")
        return self.filtered_vessels

    def get_vessels_risks(self,headers,startDate,endDate):
        self.vessels = []

        for imo in self.filtered_vessels:
            try:
                url_rc=f"https://api.kpler.com/v2/compliance/vessel-risks/{imo}?{startDate}={startDate}&{endDate}={endDate}"
                response_risk=requests.get(url_rc,headers=headers)
                response_risk.raise_for_status()
                time.sleep(1)

                if response_risk.ok:

                    json_response_risk=response_risk.json()
                   #Vessel related information
                    vessel_info = json_response_risk.get('vessel',{}).get('imo',{})
                    vessel_age = json_response_risk.get('vessel',{}).get('particulars',{}).get('yob',{})
                    #compliance related information
                    compliance_vessel = json_response_risk.get('compliance',{}).get('sanctionRisks', {}).get('sanctionedVessels', {}).get('isSanctioned', {})
                    compliance_cargo = json_response_risk.get('compliance',{}).get('sanctionRisks', {}).get('sanctionedCargo',{}).get('isSanctioned', {})
                    compliance_ismManager = json_response_risk.get('compliance',{}).get('managementRisks', {}).get('ismManager', [])
                    compliance_ismManager_true = any(company.get('endDate') is None for company in compliance_ismManager)
                    compliance_isIacs = json_response_risk.get('compliance',{}).get('managementRisks', {}).get('classified',[])
                    compliance_isIacs_true = any((company.get('endDate') is None and company.get('isIacs')) for company in compliance_isIacs)
                    compliance_pniClub = json_response_risk.get('compliance',{}).get('managementRisks', {}).get('pniClub', [])
                    compliance_isIgpi_true= any((company.get('endDate') is None and company.get('isIgpi')) for company in compliance_pniClub)
                    compliance_darkSTS = json_response_risk.get('compliance',{}).get('operationalRisks', {}).get('darkStsEvents', [])
                    compliance_darkSTS_true= any(ais.get('endDate') is None for ais in compliance_darkSTS)
                    compliance_aisSpoofs = json_response_risk.get('compliance',{}).get('operationalRisks', {}).get('aisSpoofs', [])
                    compliance_aisSpoofs_true= any(ais.get('endDate') is None for ais in compliance_aisSpoofs)
                    vessel_compliance = {'IMO': vessel_info,
                                        'YoB': vessel_age,
                                         'Vessel_IsSanctioned': compliance_vessel,
                                         'Cargo_IsSanctioned' : compliance_cargo,
                                         'ismManager' : compliance_ismManager_true,
                                         'isIacs' :compliance_isIacs_true,
                                         'isIgpi' : compliance_isIgpi_true,
                                         'darkStsEvents' : compliance_darkSTS_true,
                                         'aisSpoofs' : compliance_aisSpoofs_true
                    }

                    self.vessels.append(vessel_compliance)
            except requests.exceptions.HTTPError as e:
                print(f"\nHTTP error occurred: {e}")
                print(f"Response content: {response_risk.content.decode('utf-8')}")

        self.df_risk=pd.DataFrame(self.vessels)

        return self.df_risk


class SanctionedVessels():
    def __init__(self):
        self.grey_fleet=[]
        self.apicall=ApiCalls()

    def get_sauctioned_vessels(self):
        self.grey_fleet=[]

        for row in self.apicall.df_risk.iterrows():
            if row['Vessel_IsSanctioned'] == False:
                if row['Cargo_IsSanctioned'] == True and (row[['ismManager', 'isIacs', 'isIgpi']].eq(False).any() or row[['darkStsEvents','aisSpoofs']].any() or row['YoB'] > datetime.date.today()-timedelta(days=7305)):
                    self.grey_fleet.append(row['IMO'])
            else:
                self.grey_fleet.append(row['IMO'])
        return self.grey_fleet


class Alerting:
    def __init__(self):
        self.sauctioned=SanctionedVessels()

    def get_alerts(self):

        if len(self.sauctioned.grey_fleet) > 0:
            root = Tk()
            frm = ttk.Frame(root,borderwidth=5)
            frm.grid(padx=200, pady=100)
            root.title("Grey fleet Alert")
            ttk.Label(frm, text=f"Vessel(s) belongs to grey fleet or are sanctioned have been found with IMO(s): {self.sauctioned.grey_fleet}").grid(column=1, row=0, padx=10, pady=20)
            ttk.Button(frm, text="OK", command=root.destroy).grid(column=1, row=1,padx=10, pady=20)
            root.after(10000, root.destroy)
            root.mainloop()
        else:
            root = Tk()
            frm = ttk.Frame(root,borderwidth=5)
            frm.grid(padx=200, pady=100)
            root.title("Grey fleet Alert")
            ttk.Label(frm, text="No vessel is sanctioned or part of the grey fleet").grid(column=1, row=0, padx=10, pady=20)
            ttk.Button(frm, text="OK", command=root.destroy).grid(column=1, row=1,padx=10, pady=20)
            root.after(10000, root.destroy)
            root.mainloop()

#Make the API requests to the 2 APIs to construct your output
apicalls = ApiCalls()

apikey='Your-API-Key'
url=f"https://services.marinetraffic.com/api/exportvessels-custom-area/{apikey}?&v=2&timespan=3&vesseltypeid=35,36"
vessel_positions = apicalls.get_ais_positions(url)

headers = {'Authorization': 'Basic Your-API-key'}
startDate='2024-12-01'
endDate='2025-02-20'
vessel_risks = apicalls.get_vessels_risks(headers,startDate,endDate)


#Get the final list of vessels which are either sanctioned or in grey fleet
sanctionedvessels=SanctionedVessels()
sactioned=sanctionedvessels.get_sauctioned_vessels()

#Get an alert if a vessel is sanctioned or not.
alerting=Alerting()
alert=alerting.get_alerts()