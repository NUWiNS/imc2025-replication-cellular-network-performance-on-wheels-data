import glob
import pandas as pd
import pickle
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import sys 
import os
from collections import defaultdict
from geopy.geocoders import Nominatim
import geopy.distance
from operator import add
geolocator = Nominatim(user_agent="http")
from timezonefinder import TimezoneFinder
obj = TimezoneFinder()
from matplotlib.lines import Line2D
from earfcn.convert import earfcn2freq
import pickle as pkl
import datetime 

vz_phone_num_list = [6178231553, 6174291464, 6174294649]
tmobile_phone_num_list = [18576930597, 18576930598, 18576930599]
atnt_phone_num_list = [18573612771, 18573526798]

skip_ts_start_list = []
skip_ts_end_list = []

def earfcn_to_freq(earfcn):
    if pd.isnull(earfcn):
        return np.nan
    try:
        return earfcn2freq(earfcn)
    except:
        return np.nan
    
def downtown_measurements_mod(start_tuple, end_tuple):
    lat_lon_dt_dict = {'LA' : (34.05872013582416, -118.23766913901929), 'LV' : (36.11290509947277, -115.1731529445295), 'SLC' : (40.725262, -111.854019), 'DE' : (39.744331, -105.009438), 'CHIC' : (41.89307, -87.623787), 'INDY' : (39.768028, -86.15094), 'CLEV' : (41.5005, -81.674026), 'BOS' : (42.356740, -71.068104)}
    for key in lat_lon_dt_dict:
        distance_from_start = geopy.distance.geodesic(lat_lon_dt_dict[key], start_tuple).miles
        distance_from_end = geopy.distance.geodesic(lat_lon_dt_dict[key], end_tuple).miles
        
        # if distance_from_start <= 3 or distance_from_end <= 3:
        if distance_from_start <= 2 or distance_from_end <= 2:
            #downtown measurement
            return True
    return False

# def datetime_to_timestamp(datetime_str):
#     from datetime import datetime
#     date, time_all = datetime_str.split()
#     temp_year = date.split("-")[0]
#     temp_month = date.split("-")[1]
#     temp_date = date.split("-")[2]
#     datetime_string = temp_date + "." + temp_month + "." + temp_year + " " + time_all
#     dt_obj = datetime.strptime(datetime_string, '%d.%m.%Y %H:%M:%S.%f')
#     sec = dt_obj.timestamp() 
#     return sec


def datetime_to_timestamp(datetime_str):
    int(datetime_str.astimezone(datetime.timezone.utc).timestamp())
    return datetime_str.astimezone(datetime.timezone.utc).timestamp()

process_data = False
parse_and_plot = True
if process_data:
    tech_parse = True
    if tech_parse:
        for op in ['verizon', 'tmobile', 'atnt']:
            print("###################################################")
            print("Operator : ", op)
            if not os.path.exists("../pkls/coverage/maps/unique_dict_%s.pkl" %op):
                unique_dict = {}
                for day in range(1, 9):
                    print("Day : ", day)
                    day = str(day)
                    df = pd.read_excel('../raw_data/xcal_lte_5g_kpi_data/%s_day_%s.xlsx' %(op, day))
                    df["Qualcomm Lte/LteAdv Intrafreq Measure PCell Frequency(DL)[MHz]"] = df['LTE KPI PCell Serving EARFCN(DL)'].apply(earfcn_to_freq)
                    df_tech_lte_fiveg_freq = df[["TIME_STAMP", "Lat", "Lon", "Event Technology","Qualcomm Lte/LteAdv Intrafreq Measure PCell Frequency(DL)[MHz]", "5G KPI PCell RF Frequency [MHz]"]]
                    df_tech_lte_fiveg_freq = df_tech_lte_fiveg_freq.fillna(0)
                    print()
                    ts = list(df_tech_lte_fiveg_freq.TIME_STAMP)
                    lat = list(df_tech_lte_fiveg_freq.Lat)
                    lon = list(df_tech_lte_fiveg_freq.Lon)
                    lte_freq = list(df_tech_lte_fiveg_freq["Qualcomm Lte/LteAdv Intrafreq Measure PCell Frequency(DL)[MHz]"])
                    fiveg_freq = list(df_tech_lte_fiveg_freq["5G KPI PCell RF Frequency [MHz]"])
                    event_tech = list(df_tech_lte_fiveg_freq["Event Technology"])
                    list_idx = -1
                    for t, lt, ln, lfreq, ffreq, tech in zip(ts, lat, lon, lte_freq, fiveg_freq, event_tech):
                        list_idx+=1
                        if tech == 0 or tech == 0.0 or tech == str(0) or tech == str(0.0):
                            continue
                        modified_tech = ""
                        if "5G" in tech:
                            #find frequency 
                            if int(ffreq) == 0:
                                #look for frequency in vicinity
                                #look for frequency in vicinity
                                if list_idx > len(fiveg_freq) - 10:
                                    temp_list = fiveg_freq[list_idx - 10:list_idx]    
                                else:
                                    temp_list = fiveg_freq[list_idx+1:list_idx+10]
                                    #look only ten idx after that
                                temp_list =  [i for i in temp_list if i != 0]
                                if np.mean(temp_list) < 1000:
                                    modified_tech = "5G-low"
                                elif np.mean(temp_list) > 1000 and np.mean(temp_list) < 7000:
                                    modified_tech = "5G-sub6"
                                elif np.mean(temp_list) > 7000 and np.mean(temp_list) < 35000:
                                    modified_tech = "5G-mmWave 28 GHz"
                                elif np.mean(temp_list) > 35000:
                                    modified_tech = "5G-mmWave 39 GHz"
                            else:
                                #found frequency
                                if int(ffreq) < 1000:
                                    modified_tech = "5G-low"
                                elif int(ffreq) > 1000 and int(ffreq) < 7000:
                                    modified_tech = "5G-sub6"
                                elif int(ffreq) > 7000 and int(ffreq) < 35000:
                                    modified_tech = "5G-mmWave 28 GHz"
                                elif int(ffreq) > 35000:
                                    modified_tech = "5G-mmWave 39 GHz"
                        elif "LTE" in tech:
                            #find frequency 
                            if int(lfreq) == 0:
                                #look for frequency in vicinity
                                if list_idx > len(lte_freq) - 10:
                                    temp_list = lte_freq[list_idx - 10:list_idx]    
                                else:
                                    temp_list = lte_freq[list_idx+1:list_idx+10]
                                    #look only ten idx after that
                                temp_list =  [i for i in temp_list if i != 0]
                                if np.mean(temp_list) < 1000:
                                    modified_tech = "LTE"
                                elif np.mean(temp_list) > 1000:
                                    modified_tech = "LTE-A"
                            else:
                                #found frequency
                                if int(lfreq) < 1000:
                                    modified_tech = "LTE"
                                elif int(lfreq) > 1000:
                                    modified_tech = "LTE-A"
                        if modified_tech == "":
                            continue

                        if (lt, ln) in list(unique_dict.keys()):
                            unique_dict[(lt, ln)].append(modified_tech)
                        else:
                            unique_dict[(lt, ln)] = [modified_tech]

                    print("-------------------")
                for key in unique_dict.keys():
                    unique_dict[key] = max(unique_dict[key],key=unique_dict[key].count)

                fh = open("../pkls/coverage/unique_dict_%s.pkl" %op, "wb")
                pkl.dump(unique_dict, fh)
                fh.close()

    tech_parse_speed_distance = True
    if tech_parse_speed_distance:
        total_dist_operator = {}
        total_time_operator = {}
        breakup_dist_operator = {}
        total_dist_tz_operator = {}
        total_time_tz_operator = {}
        breakup_dist_tz_operator = {}
        total_dist_area_operator = {}
        breakup_dist_area_operator = {}
        total_dist_speed_operator = {}
        total_time_speed_operator = {}
        breakup_dist_speed_operator = {}
        speed_tech_operator = {}
        for op in ['verizon', 'tmobile', 'atnt']:
            print("###################################################")
            print("Operator : ", op)
            if not os.path.exists("../pkls/coverage/bars/unique_dict_%s.pkl" %op):
                unique_dict = {}
                for day in range(1, 9):
                    print("Day : ", day)
                    day = str(day)
                    df = pd.read_excel('../raw_data/xcal_lte_5g_kpi_data%s_day_%s.xlsx' %(op, day))
                    df.drop(df.tail(8).index,inplace=True)
                    df['TIME_STAMP'] = df['TIME_STAMP'].apply(datetime_to_timestamp)
                    df["Qualcomm Lte/LteAdv Intrafreq Measure PCell Frequency(DL)[MHz]"] = df['LTE KPI PCell Serving EARFCN(DL)'].apply(earfcn_to_freq)
                    df_tech_lte_fiveg_freq = df[["TIME_STAMP", "Lat", "Lon", "Event Technology","Qualcomm Lte/LteAdv Intrafreq Measure PCell Frequency(DL)[MHz]", "5G KPI PCell RF Frequency [MHz]"]]
                    df_tech_lte_fiveg_freq = df_tech_lte_fiveg_freq.fillna(0)
                    start_area_df_time = df_tech_lte_fiveg_freq.TIME_STAMP.iloc[0] - 3600
                    end_area_df_time = df_tech_lte_fiveg_freq.TIME_STAMP.iloc[-1]

                    df_area = pd.read_csv('/home/moinakgh/csv_ho/driving_trip_lax_bos_2024/bos_la_weather_area/data/area.csv')
                    df_area = df_area[(df_area['utc_ts'] >= start_area_df_time) & (df_area['utc_ts'] <= end_area_df_time)]
                    df_area = df_area.rename(columns={'utc_ts' : 'TIME_STAMP'})
                    df_tech_lte_fiveg_freq = pd.concat([df_tech_lte_fiveg_freq, df_area])
                    df_tech_lte_fiveg_freq = df_tech_lte_fiveg_freq.sort_values(by=["TIME_STAMP"]) 
                    df_tech_lte_fiveg_freq['value'] = df_tech_lte_fiveg_freq['value'].ffill()
                    df_tech_lte_fiveg_freq['value'] = df_tech_lte_fiveg_freq['value'].fillna(0)
                    df_tech_lte_fiveg_freq = df_tech_lte_fiveg_freq.fillna(0)
                    ts = list(df_tech_lte_fiveg_freq.TIME_STAMP)
                    lat = list(df_tech_lte_fiveg_freq.Lat)
                    lon = list(df_tech_lte_fiveg_freq.Lon)
                    lte_freq = list(df_tech_lte_fiveg_freq["Qualcomm Lte/LteAdv Intrafreq Measure PCell Frequency(DL)[MHz]"])
                    fiveg_freq = list(df_tech_lte_fiveg_freq["5G KPI PCell RF Frequency [MHz]"])
                    event_tech = list(df_tech_lte_fiveg_freq["Event Technology"])
                    area_type = list(df_tech_lte_fiveg_freq["value"])
                    list_idx = -1
                    for t, lt, ln, lfreq, ffreq, tech, area in zip(ts, lat, lon, lte_freq, fiveg_freq, event_tech, area_type):
                        list_idx+=1
                        if tech == 0 or tech == 0.0 or tech == str(0) or tech == str(0.0):
                            continue
                        modified_tech = ""
                        if "5G" in tech:
                            #find frequency 
                            if int(ffreq) == 0:
                                #look for frequency in vicinity
                                #look for frequency in vicinity
                                if list_idx > len(fiveg_freq) - 10:
                                    temp_list = fiveg_freq[list_idx - 10:list_idx]    
                                else:
                                    temp_list = fiveg_freq[list_idx+1:list_idx+10]
                                    #look only ten idx after that
                                temp_list =  [i for i in temp_list if i != 0]
                                if np.mean(temp_list) < 1000:
                                    modified_tech = "5G-low"
                                elif np.mean(temp_list) > 1000 and np.mean(temp_list) < 7000:
                                    modified_tech = "5G-sub6"
                                elif np.mean(temp_list) > 7000 and np.mean(temp_list) < 35000:
                                    modified_tech = "5G-mmWave 28 GHz"
                                elif np.mean(temp_list) > 35000:
                                    modified_tech = "5G-mmWave 39 GHz"
                            else:
                                #found frequency
                                if int(ffreq) < 1000:
                                    modified_tech = "5G-low"
                                elif int(ffreq) > 1000 and int(ffreq) < 7000:
                                    modified_tech = "5G-sub6"
                                elif int(ffreq) > 7000 and int(ffreq) < 35000:
                                    modified_tech = "5G-mmWave 28 GHz"
                                elif int(ffreq) > 35000:
                                    modified_tech = "5G-mmWave 39 GHz"
                        elif "LTE" in tech:
                            #find frequency 
                            if int(lfreq) == 0:
                                #look for frequency in vicinity
                                if list_idx > len(lte_freq) - 10:
                                    temp_list = lte_freq[list_idx - 10:list_idx]    
                                else:
                                    temp_list = lte_freq[list_idx+1:list_idx+10]
                                    #look only ten idx after that
                                temp_list =  [i for i in temp_list if i != 0]
                                if np.mean(temp_list) < 1000:
                                    modified_tech = "LTE"
                                elif np.mean(temp_list) > 1000:
                                    modified_tech = "LTE-A"
                            else:
                                #found frequency
                                if int(lfreq) < 1000:
                                    modified_tech = "LTE"
                                elif int(lfreq) > 1000:
                                    modified_tech = "LTE-A"
                        if modified_tech == "":
                            continue
                        if "39 GHz" in modified_tech and t in range(1660432274, 1660433472):
                            continue
                        if (t, lt, ln, area) in list(unique_dict.keys()):
                            pass
                        else:
                            unique_dict[(t, lt, ln, area)] = modified_tech
            
                fh = open("../pkls/coverage/bars/unique_dict_%s.pkl" %op, "wb")
                pkl.dump(unique_dict, fh)
                fh.close()

            else:
                fh = open("../pkls/coverage/bars/unique_dict_%s.pkl" %op, "rb")
                unique_dict = pkl.load(fh)
                fh.close()
            new_dict = defaultdict(list)
            for key, val in sorted(unique_dict.items()):
                new_dict[val].append(key)

            if 1:        
                total_dist = 0
                total_time = 0
                dist_dict = {'5G-sub6' : 0, 'LTE-A' : 0, '5G-mmWave 28 GHz' : 0, '5G-low' : 0, 'LTE' : 0, '5G-mmWave 39 GHz' : 0}
                for tech in new_dict.keys():
                    ts_sorted_list = sorted(new_dict[tech], key=lambda x: x[0])
                    prev_ts, prev_lat, prev_lon, area_type = ts_sorted_list[0]
                    skip = 0
                    for tple in ts_sorted_list[1:]:
                        cur_ts, cur_lat, cur_lon, cur_area = tple
                        if (cur_ts - prev_ts) < 0:
                            #not sorted
                            print("Ehh! !")
                        elif (cur_ts - prev_ts) > 5:
                            # probably different run
                            # do nothing
                            # print("Well it can happen")
                            pass
                        else:
                            distance = geopy.distance.geodesic((cur_lat, cur_lon), (prev_lat, prev_lon)).miles
                            if distance > 0.3:
                                print("Ehh! !")
                            else:
                                total_dist+=distance
                                total_time+=(cur_ts - prev_ts)
                                dist_dict[tech]+=distance
                        prev_ts, prev_lat, prev_lon, prev_area = tple

                total_dist_operator[op] = total_dist   
                total_time_operator[op] = total_time
                breakup_dist_operator[op] = dist_dict
        
            if 1:    
                tz_name_dict = {'America/Los_Angeles' : "PacificTime", 'America/Denver' : "MountainTime", 'America/Chicago' : "CentralTime", 'America/New_York' : "EasternTime" }    
                total_dist = {'PacificTime' : 0, 'MountainTime' : 0, 'CentralTime' : 0, 'EasternTime' : 0}
                total_time = {'PacificTime' : 0, 'MountainTime' : 0, 'CentralTime' : 0, 'EasternTime' : 0}
                dist_dict = {'5G-sub6' : {'PacificTime' : 0, 'MountainTime' : 0, 'CentralTime' : 0, 'EasternTime' : 0} , 'LTE-A' : {'PacificTime' : 0, 'MountainTime' : 0, 'CentralTime' : 0, 'EasternTime' : 0} , '5G-mmWave 28 GHz' : {'PacificTime' : 0, 'MountainTime' : 0, 'CentralTime' : 0, 'EasternTime' : 0} , '5G-low' : {'PacificTime' : 0, 'MountainTime' : 0, 'CentralTime' : 0, 'EasternTime' : 0}, 'LTE' : {'PacificTime' : 0, 'MountainTime' : 0, 'CentralTime' : 0, 'EasternTime' : 0}, '5G-mmWave 39 GHz' : {'PacificTime' : 0, 'MountainTime' : 0, 'CentralTime' : 0, 'EasternTime' : 0}}
                for tech in new_dict.keys():
                    ts_sorted_list = sorted(new_dict[tech], key=lambda x: x[0])
                    prev_ts, prev_lat, prev_lon, area_type = ts_sorted_list[0]
                    skip = 0
                    for tple in ts_sorted_list[1:]:
                        cur_ts, cur_lat, cur_lon, cur_area = tple
                        if (cur_ts - prev_ts) < 0:
                            #not sorted
                            print("Ehh! !")
                            # sys.exit(1)
                        elif (cur_ts - prev_ts) > 5:
                            # probably different run
                            # do nothing
                            # print("Well it can happen")
                            pass
                        else:
                            distance = geopy.distance.geodesic((cur_lat, cur_lon), (prev_lat, prev_lon)).miles
                            if distance > 0.3:
                                print("Ehh! !")
                            else:
                                temp_tz = obj.timezone_at(lng=cur_lon, lat=cur_lat)
                                if "Indiana" in temp_tz:
                                    temp_tz = 'America/New_York'
                                elif temp_tz == 'America/Phoenix':
                                    temp_tz = 'America/Denver'
                                if temp_tz not in list(tz_name_dict.keys()) and temp_tz != 'Etc/GMT':
                                    print("Ehh! ")
                                if temp_tz in list(tz_name_dict.keys()):
                                    timezone = tz_name_dict[temp_tz]
                                    total_dist[timezone]+=distance
                                    total_time[timezone]+=(cur_ts - prev_ts)
                                    dist_dict[tech][timezone]+=distance
                        prev_ts, prev_lat, prev_lon, prev_area = tple

                total_dist_tz_operator[op] = total_dist
                total_time_tz_operator[op] = total_time
                breakup_dist_tz_operator[op] = dist_dict

            if 1:    
                total_dist = {'suburban' : 0, 'urban' : 0, 'rural' : 0, 'unclassified': 0}
                dist_dict = {'5G-sub6' : {'suburban' : 0, 'urban' : 0, 'rural' : 0, 'unclassified': 0} , 'LTE-A' : {'suburban' : 0, 'urban' : 0, 'rural' : 0, 'unclassified': 0} , '5G-mmWave 28 GHz' : {'suburban' : 0, 'urban' : 0, 'rural' : 0, 'unclassified': 0} , '5G-low' : {'suburban' : 0, 'urban' : 0, 'rural' : 0, 'unclassified': 0}, 'LTE' : {'suburban' : 0, 'urban' : 0, 'rural' : 0, 'unclassified': 0}, '5G-mmWave 39 GHz' : {'suburban' : 0, 'urban' : 0, 'rural' : 0, 'unclassified': 0}}
                for tech in new_dict.keys():
                    ts_sorted_list = sorted(new_dict[tech], key=lambda x: x[0])
                    prev_ts, prev_lat, prev_lon, area_type = ts_sorted_list[0]
                    skip = 0
                    for tple in ts_sorted_list[1:]:
                        cur_ts, cur_lat, cur_lon, cur_area = tple
                        if (cur_ts - prev_ts) < 0:
                            #not sorted
                            print("Ehh! !")
                            # sys.exit(1)
                        elif (cur_ts - prev_ts) > 5:
                            # probably different run
                            # do nothing
                            # print("Well it can happen")
                            pass
                        else:
                            distance = geopy.distance.geodesic((cur_lat, cur_lon), (prev_lat, prev_lon)).miles
                            if distance > 0.3:
                                print("Ehh! !")
                            else:
                                if cur_area == 0:
                                    cur_area = 'unclassified'

                                total_dist[cur_area]+=distance
                                dist_dict[tech][cur_area]+=distance
                        prev_ts, prev_lat, prev_lon, prev_area = tple

                total_dist_area_operator[op] = total_dist   
                breakup_dist_area_operator[op] = dist_dict

            if 1:    
                tech_order_dict = {'5G-sub6' : 4, 'LTE-A' : 2, '5G-mmWave 28 GHz' : 5, '5G-low' : 3, 'LTE' : 1, '5G-mmWave 39 GHz' : 5}
                total_dist = {'0-20' : 0, '20-60' : 0, '60+' : 0}
                total_time = {'0-20' : 0, '20-60' : 0, '60+' : 0}
                dist_dict = {'5G-sub6' : {'0-20' : 0, '20-60' : 0, '60+' : 0}, 'LTE-A' : {'0-20' : 0, '20-60' : 0, '60+' : 0} , '5G-mmWave 28 GHz' : {'0-20' : 0, '20-60' : 0, '60+' : 0} , '5G-low' : {'0-20' : 0, '20-60' : 0, '60+' : 0}, 'LTE' : {'0-20' : 0, '20-60' : 0, '60+' : 0}, '5G-mmWave 39 GHz' : {'0-20' : 0, '20-60' : 0, '60+' : 0}}
                speed_tech_tuple = []
                for tech in new_dict.keys():
                    ts_sorted_list = sorted(new_dict[tech], key=lambda x: x[0])
                    prev_ts, prev_lat, prev_lon, area_type = ts_sorted_list[0]
                    skip = 0
                    for tple in ts_sorted_list[1:]:
                        cur_ts, cur_lat, cur_lon, cur_area = tple
                        if (cur_ts - prev_ts) < 0:
                            #not sorted
                            print("Ehh! !")
                            # sys.exit(1)
                        elif (cur_ts - prev_ts) > 5:
                            # probably different run
                            # do nothing
                            # print("Well it can happen")
                            pass
                        else:
                            
                            distance = geopy.distance.geodesic((cur_lat, cur_lon), (prev_lat, prev_lon)).miles
                            if distance > 0.3:
                                print("Ehh! !")
                            else:
                                if cur_ts - prev_ts == 0:
                                    speed = (distance/ (prev_diff_ts)) * 3600
                                else:
                                    speed = (distance/ (cur_ts - prev_ts)) * 3600
                                dt_measurement = downtown_measurements_mod((cur_lat, cur_lon), (prev_lat, prev_lon))
                                if dt_measurement and speed > 20:
                                    speed_dict_key = '0-20'
                                    import random
                                    speed_tech_tuple.append([speed, random.randint(0, 19)])
                                else:
                                    if speed <= 20:
                                        speed_dict_key = '0-20'
                                    elif speed > 20 and speed <= 60:
                                        speed_dict_key = '20-60'
                                    elif speed > 60:
                                        speed_dict_key = '60+'
                                    if 'mmWave' in tech and speed_dict_key == '20-60':
                                        a = 1 
                                    speed_tech_tuple.append([speed, tech_order_dict[tech]])
                                total_dist[speed_dict_key]+=distance
                                total_time[speed_dict_key]+=(cur_ts - prev_ts)
                                dist_dict[tech][speed_dict_key]+=distance
                        prev_diff_ts = cur_ts - prev_ts
                        prev_ts, prev_lat, prev_lon, prev_area = tple

                total_dist_speed_operator[op] = total_dist
                total_time_speed_operator[op] = total_time
                breakup_dist_speed_operator[op] = dist_dict
                speed_tech_operator[op] = speed_tech_tuple

        fh = open("../pkls/coverage/bars/tz_dist_coverage.pkl", "wb")
        pkl.dump([total_dist_operator, breakup_dist_operator, total_dist_tz_operator, breakup_dist_tz_operator, total_dist_speed_operator, breakup_dist_speed_operator, speed_tech_operator, total_dist_area_operator, breakup_dist_area_operator], fh)
        fh.close()

        # Save the total time operator data
        fh = open("../pkls/coverage/bars/tz_time_coverage.pkl", "wb")
        pkl.dump([total_time_operator, total_time_tz_operator, total_time_speed_operator], fh)
        fh.close()

if parse_and_plot:
    filehandler = open("../pkls/coverage/bars/tz_dist_coverage.pkl", "rb")
    total_dist_operator, breakup_dist_operator, total_dist_tz_operator, breakup_dist_tz_operator, total_dist_speed_operator, breakup_dist_speed_operator, speed_tech_operator, total_dist_area_operator, breakup_dist_area_operator = pickle.load(filehandler)
    filehandler.close()
    
    fh = open("../pkls/coverage/bars/tz_time_coverage.pkl", "rb")
    total_time_operator, total_time_tz_operator, total_time_speed_operator = pkl.load(fh)
    fh.close()

    # figure 2a
    tech_list = ['LTE', 'LTE-A', '5G-low', '5G-sub6', '5G-mmWave 28 GHz', '5G-mmWave 39 GHz']
    op_wise_dist_percentage = {"verizon" : {}, "tmobile" : {}, "atnt" : {}}
    labels = ["Verizon", "T-Mobile", "AT&T"]
    op_list = ["verizon", "tmobile", "atnt"]
    width = 0.35
    for op in total_dist_operator.keys():
        total_dist = total_dist_operator[op]
        for tech in tech_list:
            op_wise_dist_percentage[op][tech] = (breakup_dist_operator[op][tech] / total_dist) * 100
    tech_dict = {'LTE' : [], 'LTE-A' : [], '5G-low' : [], '5G-sub6' : [], '5G-mmWave 28 GHz' : [], '5G-mmWave 39 GHz' : []}
    label_dict = {'LTE' : 'LTE', 'LTE-A' : 'LTE-A', '5G-low' : '5G-low', '5G-sub6' : '5G-mid', '5G-mmWave 28 GHz' : '5G-mmWave (28 GHz)', '5G-mmWave 39 GHz' : '5G-mmWave (39 GHz)'}
    color_dict = {"LTE" : "#08710C", "LTE-A" : "#70CA32", "5G-low" : "#F3FF33", "5G-sub6" : "#FFB233", "5G-mmWave 28 GHz" : "#FF4629", "5G-mmWave 39 GHz" : "#CB0404" }
    # color_dict = {"LTE" : "navy", "LTE-A" : "deepskyblue", "5G-low" : "green", "5G-sub6" : "yellow", "5G-mmWave 28 GHz" : "red", "5G-mmWave 39 GHz" : "maroon" }
    for tech in tech_list:
        for op in op_list:
            tech_dict[tech].append(op_wise_dist_percentage[op][tech])
    fig, ax = plt.subplots(figsize=(4, 5.5))
    count = 0
    for tech in tech_dict.keys():
        if count == 0:
            ax.bar(labels, tech_dict[tech], width, label=label_dict[tech], color=color_dict[tech])
            prev = tech_dict[tech]
        else:
            ax.bar(labels, tech_dict[tech], width, label=label_dict[tech], bottom=prev, color=color_dict[tech])
            temp = []
            for i in range(0, len(prev)):
                temp.append(prev[i] + tech_dict[tech][i])
            prev = temp.copy()
        count+=1
    # ax.set_ylabel("Percentage coverage per mile (%)")
    ax.set_ylabel("Fraction of miles covered (%)")
    # ax.set_xlabel("Cellular Operator")
    ax.set_ylim(ymax=120)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    plt.tight_layout()
    plt.savefig("../plots/coverage/fig_2a.pdf")
    plt.close()

    # figure 2c
    #adding atnt mmWave 39 GHz DL/UL distance which got missed
    fig, ax = plt.subplots(1, 4, figsize=(15, 7), sharey=True)
    graph_no = 0
    tz_name_dict = {'PacificTime' : "Pacific Time", 'MountainTime' : "Mountain Time", 'CentralTime' : "Central Time", 'EasternTime' : "Eastern Time"}
    for tz in ['PacificTime', 'MountainTime', 'CentralTime', 'EasternTime']:
        tech_list = ['LTE', 'LTE-A', '5G-low', '5G-sub6', '5G-mmWave 28 GHz', '5G-mmWave 39 GHz']
        op_wise_dist_percentage = {"verizon" : {}, "tmobile" : {}, "atnt" : {}}
        labels = ["Verizon", "T-Mobile", "AT&T"]
        op_list = ["verizon", "tmobile", "atnt"]
        width = 0.35
        for op in total_dist_tz_operator.keys():
            total_dist = total_dist_tz_operator[op][tz]
            for tech in tech_list:
                op_wise_dist_percentage[op][tech] = (breakup_dist_tz_operator[op][tech][tz] / total_dist) * 100
        tech_dict = {'LTE' : [], 'LTE-A' : [], '5G-low' : [], '5G-sub6' : [], '5G-mmWave 28 GHz' : [], '5G-mmWave 39 GHz' : []}
        label_dict = {'LTE' : 'LTE', 'LTE-A' : 'LTE-A', '5G-low' : '5G-low', '5G-sub6' : '5G-mid', '5G-mmWave 28 GHz' : '5G-mmWave (28 GHz)', '5G-mmWave 39 GHz' : '5G-mmWave (39 GHz)'}
        color_dict = {"LTE" : "navy", "LTE-A" : "deepskyblue", "5G-low" : "green", "5G-sub6" : "yellow", "5G-mmWave 28 GHz" : "red", "5G-mmWave 39 GHz" : "maroon" }
        color_dict = {"LTE" : "#08710C", "LTE-A" : "#70CA32", "5G-low" : "#F3FF33", "5G-sub6" : "#FFB233", "5G-mmWave 28 GHz" : "#FF4629", "5G-mmWave 39 GHz" : "#CB0404" }
        for tech in tech_list:
            for op in op_list:
                tech_dict[tech].append(op_wise_dist_percentage[op][tech])
        count = 0
        for tech in tech_dict.keys():
            if count == 0:
                ax[graph_no].bar(labels, tech_dict[tech], width, label=label_dict[tech], color=color_dict[tech])
                prev = tech_dict[tech]
            else:
                ax[graph_no].bar(labels, tech_dict[tech], width, label=label_dict[tech], bottom=prev, color=color_dict[tech])
                temp = []
                for i in range(0, len(prev)):
                    temp.append(prev[i] + tech_dict[tech][i])
                prev = temp.copy()
            count+=1
        # if graph_no == 0:
        #     ax[0].set_ylabel("Percentage coverage per mile (%)")
        #     ax[0].legend(loc = "upper left")
        # ax[graph_no].set_xlabel("Cellular Operator")
        ax[graph_no].set_ylim(ymax=120)
        ax[graph_no].set_title(tz_name_dict[tz], fontsize=20, fontweight='bold')
        ax[graph_no].set_yticks([0, 20, 40, 60, 80, 100])
        ax[graph_no].tick_params(axis='x', labelsize=18)
        if graph_no == 0:
            custom_lines = [Line2D([0], [0], color="#08710C", lw=6), Line2D([0], [0], color="#70CA32", lw=6),]
            ax[graph_no].legend(custom_lines, ['LTE', 'LTE-A'], fontsize=18, loc='upper center', ncols=1)
        elif graph_no == 1:
            custom_lines = [Line2D([0], [0], color="#F3FF33", lw=6), Line2D([0], [0], color= "#FFB233", lw=6),]
            ax[graph_no].legend(custom_lines, ['5G-low', '5G-mid'], fontsize=18, loc='upper center', ncols=1)
        elif graph_no == 2:
            custom_lines = [Line2D([0], [0], color="#FF4629", lw=6)]
            ax[graph_no].legend(custom_lines, ['5G-mmWave\n(28 GHz)'], fontsize=18, loc='upper center', ncols=1)
        else:
            custom_lines = [Line2D([0], [0], color="#CB0404", lw=6)]
            ax[graph_no].legend(custom_lines, ['5G-mmWave\n(39 GHz)'], fontsize=18, loc='upper center', ncols=1)
        graph_no+=1
    plt.tight_layout()
    plt.savefig("../plots/coverage/fig_2c.pdf")
    plt.close()
    print()

    # figure 2d
    fig, ax = plt.subplots(1, 3, figsize=(11, 6), sharey=True)
    graph_no = 0
    tz_name_dict = {'PacificTime' : "Pacific Time", 'MountainTime' : "Mountain Time", 'CentralTime' : "Central Time", 'EasternTime' : "Eastern Time"}
    for speed_bin in ['0-20', '20-60', '60+']:
        tech_list = ['LTE', 'LTE-A', '5G-low', '5G-sub6', '5G-mmWave 28 GHz', '5G-mmWave 39 GHz']
        op_wise_dist_percentage = {"verizon" : {}, "tmobile" : {}, "atnt" : {}}
        labels = ["Verizon", "T-Mobile", "AT&T"]
        op_list = ["verizon", "tmobile", "atnt"]
        width = 0.35
        for op in total_dist_speed_operator.keys():
            total_dist = total_dist_speed_operator[op][speed_bin]
            for tech in tech_list:
                op_wise_dist_percentage[op][tech] = (breakup_dist_speed_operator[op][tech][speed_bin] / total_dist) * 100
        tech_dict = {'LTE' : [], 'LTE-A' : [], '5G-low' : [], '5G-sub6' : [], '5G-mmWave 28 GHz' : [], '5G-mmWave 39 GHz' : []}
        label_dict = {'LTE' : 'LTE', 'LTE-A' : 'LTE-A', '5G-low' : '5G-low', '5G-sub6' : '5G-mid', '5G-mmWave 28 GHz' : '5G-mmWave (28 GHz)', '5G-mmWave 39 GHz' : '5G-mmWave (39 GHz)'}
        color_dict = {"LTE" : "navy", "LTE-A" : "deepskyblue", "5G-low" : "green", "5G-sub6" : "yellow", "5G-mmWave 28 GHz" : "red", "5G-mmWave 39 GHz" : "maroon" }
        color_dict = {"LTE" : "#08710C", "LTE-A" : "#70CA32", "5G-low" : "#F3FF33", "5G-sub6" : "#FFB233", "5G-mmWave 28 GHz" : "#FF4629", "5G-mmWave 39 GHz" : "#CB0404" }
        for tech in tech_list:
            for op in op_list:
                tech_dict[tech].append(op_wise_dist_percentage[op][tech])
        count = 0
        for tech in tech_dict.keys():
            if count == 0:
                ax[graph_no].bar(labels, tech_dict[tech], width, label=label_dict[tech], color=color_dict[tech])
                prev = tech_dict[tech]
            else:
                ax[graph_no].bar(labels, tech_dict[tech], width, label=label_dict[tech], bottom=prev, color=color_dict[tech])
                temp = []
                for i in range(0, len(prev)):
                    temp.append(prev[i] + tech_dict[tech][i])
                prev = temp.copy()
            count+=1
        if graph_no == 0:
            ax[0].set_ylabel("Fraction of miles covered (%)")
        ax[graph_no].set_ylim(ymax=120)
        ax[graph_no].set_title(speed_bin + " (miles/hr)", fontsize=20, fontweight='bold')
        ax[graph_no].set_yticks([0, 20, 40, 60, 80, 100])
        ax[graph_no].tick_params(axis='x', labelsize=18)
        graph_no+=1
    plt.tight_layout()
    plt.savefig("../plots/coverage/fig_2d.pdf")
    plt.close()

    # figure 2d
    fig, ax = plt.subplots(1, 3, figsize=(11, 6), sharey=True)
    graph_no = 0
    tz_name_dict = {'PacificTime' : "Pacific Time", 'MountainTime' : "Mountain Time", 'CentralTime' : "Central Time", 'EasternTime' : "Eastern Time"}
    for speed_bin in ['0-20', '20-60', '60+']:
        tech_list = ['LTE', 'LTE-A', '5G-low', '5G-sub6', '5G-mmWave 28 GHz', '5G-mmWave 39 GHz']
        op_wise_dist_percentage = {"verizon" : {}, "tmobile" : {}, "atnt" : {}}
        labels = ["Verizon", "T-Mobile", "AT&T"]
        op_list = ["verizon", "tmobile", "atnt"]
        width = 0.35
        for op in total_dist_speed_operator.keys():
            total_dist = total_dist_speed_operator[op][speed_bin]
            for tech in tech_list:
                op_wise_dist_percentage[op][tech] = (breakup_dist_speed_operator[op][tech][speed_bin] / total_dist) * 100
        tech_dict = {'LTE' : [], 'LTE-A' : [], '5G-low' : [], '5G-sub6' : [], '5G-mmWave 28 GHz' : [], '5G-mmWave 39 GHz' : []}
        label_dict = {'LTE' : 'LTE', 'LTE-A' : 'LTE-A', '5G-low' : '5G-low', '5G-sub6' : '5G-mid', '5G-mmWave 28 GHz' : '5G-mmWave (28 GHz)', '5G-mmWave 39 GHz' : '5G-mmWave (39 GHz)'}
        color_dict = {"LTE" : "navy", "LTE-A" : "deepskyblue", "5G-low" : "green", "5G-sub6" : "yellow", "5G-mmWave 28 GHz" : "red", "5G-mmWave 39 GHz" : "maroon" }
        color_dict = {"LTE" : "#08710C", "LTE-A" : "#70CA32", "5G-low" : "#F3FF33", "5G-sub6" : "#FFB233", "5G-mmWave 28 GHz" : "#FF4629", "5G-mmWave 39 GHz" : "#CB0404" }
        for tech in tech_list:
            for op in op_list:
                tech_dict[tech].append(op_wise_dist_percentage[op][tech])
        count = 0
        for tech in tech_dict.keys():
            if count == 0:
                ax[graph_no].bar(labels, tech_dict[tech], width, label=label_dict[tech], color=color_dict[tech])
                prev = tech_dict[tech]
            else:
                ax[graph_no].bar(labels, tech_dict[tech], width, label=label_dict[tech], bottom=prev, color=color_dict[tech])
                temp = []
                for i in range(0, len(prev)):
                    temp.append(prev[i] + tech_dict[tech][i])
                prev = temp.copy()
            count+=1
        if graph_no == 0:
            ax[0].set_ylabel("Fraction of miles covered (%)")
        ax[graph_no].set_ylim(ymax=120)
        ax[graph_no].set_title(speed_bin + " (miles/hr)", fontsize=20, fontweight='bold')
        ax[graph_no].set_yticks([0, 20, 40, 60, 80, 100])
        ax[graph_no].tick_params(axis='x', labelsize=18)
        graph_no+=1
    plt.tight_layout()
    plt.savefig("../plots/coverage/fig_2d.pdf")
    plt.close()

    # area type
    fig, ax = plt.subplots(1, 3, figsize=(11, 6), sharey=True)
    graph_no = 0
    for area_bin in ['urban', 'suburban', 'rural']:
        tech_list = ['LTE', 'LTE-A', '5G-low', '5G-sub6', '5G-mmWave 28 GHz', '5G-mmWave 39 GHz']
        op_wise_dist_percentage = {"verizon" : {}, "tmobile" : {}, "atnt" : {}}
        labels = ["Verizon", "T-Mobile", "AT&T"]
        op_list = ["verizon", "tmobile", "atnt"]
        width = 0.35
        for op in total_dist_area_operator.keys():
            total_dist = total_dist_area_operator[op][area_bin]
            for tech in tech_list:
                op_wise_dist_percentage[op][tech] = (breakup_dist_area_operator[op][tech][area_bin] / total_dist) * 100
        tech_dict = {'LTE' : [], 'LTE-A' : [], '5G-low' : [], '5G-sub6' : [], '5G-mmWave 28 GHz' : [], '5G-mmWave 39 GHz' : []}
        label_dict = {'LTE' : 'LTE', 'LTE-A' : 'LTE-A', '5G-low' : '5G-low', '5G-sub6' : '5G-mid', '5G-mmWave 28 GHz' : '5G-mmWave (28 GHz)', '5G-mmWave 39 GHz' : '5G-mmWave (39 GHz)'}
        color_dict = {"LTE" : "navy", "LTE-A" : "deepskyblue", "5G-low" : "green", "5G-sub6" : "yellow", "5G-mmWave 28 GHz" : "red", "5G-mmWave 39 GHz" : "maroon" }
        color_dict = {"LTE" : "#08710C", "LTE-A" : "#70CA32", "5G-low" : "#F3FF33", "5G-sub6" : "#FFB233", "5G-mmWave 28 GHz" : "#FF4629", "5G-mmWave 39 GHz" : "#CB0404" }
        
        for tech in tech_list:
            for op in op_list:
                tech_dict[tech].append(op_wise_dist_percentage[op][tech])
        count = 0
        for tech in tech_dict.keys():
            if count == 0:
                ax[graph_no].bar(labels, tech_dict[tech], width, label=label_dict[tech], color=color_dict[tech])
                prev = tech_dict[tech]
            else:
                ax[graph_no].bar(labels, tech_dict[tech], width, label=label_dict[tech], bottom=prev, color=color_dict[tech])
                temp = []
                for i in range(0, len(prev)):
                    temp.append(prev[i] + tech_dict[tech][i])
                prev = temp.copy()
            count+=1
        if graph_no == 0:
            ax[0].set_ylabel("Fraction of miles covered (%)")
        ax[graph_no].set_ylim(ymax=120)
        ax[graph_no].set_title(area_bin, fontsize=20, fontweight='bold')
        ax[graph_no].set_yticks([0, 20, 40, 60, 80, 100])
        ax[graph_no].tick_params(axis='x', labelsize=18)
        graph_no+=1
    plt.tight_layout()
    plt.savefig("../plots/coverage/coverage_area_type.pdf")
    plt.close()