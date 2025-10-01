import glob
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from operator import add
# from datetime import datetime
import matplotlib.lines as mlines
import datetime
from datetime import timezone, timedelta
import pickle as pkl
import plotly.express as px
import plotly.graph_objects as go
from earfcn.convert import earfcn2freq
from timezonefinder import TimezoneFinder
obj = TimezoneFinder()
import geopy.distance
import time
from collections import OrderedDict
from collections import Counter
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import warnings
from matplotlib.lines import Line2D
warnings.filterwarnings("ignore")

def downtown_measurements_mod(current_coordinate):
    lat_lon_dt_dict = {'LA' : (34.05872013582416, -118.23766913901929), 'LV' : (36.11290509947277, -115.1731529445295), 'SLC' : (40.725262, -111.854019), 'DE' : (39.744331, -105.009438), 'CHIC' : (41.89307, -87.623787), 'INDY' : (39.768028, -86.15094), 'CLEV' : (41.5005, -81.674026), 'BOS' : (42.356740, -71.068104)}
    # lat_lon_dt_dict = {'BOS' : (42.356740, -71.068104)}
    for key in lat_lon_dt_dict:
        distance_from_start = geopy.distance.geodesic(lat_lon_dt_dict[key], current_coordinate).miles
        
        if distance_from_start <= 4:
            #downtown measurement
            return True
    return False

def earfcn_to_freq(earfcn):
    if pd.isnull(earfcn):
        return np.nan
    try:
        return earfcn2freq(earfcn)
    except:
        return np.nan

def find_directories_with_keyword(base_dir, keyword, file_extension):
    matching_dirs = set()  # Use a set to avoid duplicates

    for root, _, files in os.walk(base_dir):
        for file in files:
            if keyword in file and file.endswith(file_extension):
                matching_dirs.add(root)
                break  # No need to check further files in this directory

    return sorted(matching_dirs)

def datetime_to_timestamp(datetime_str):
    int(datetime_str.astimezone(datetime.timezone.utc).timestamp())
    return datetime_str.astimezone(datetime.timezone.utc).timestamp()


def check_is_wavelength(lat, lon): 
    """ Given a run, return whether a run is with AWS Wavelength. Assume edge server is used when the run is near the cities. """ 
    coord_city_arr = [ [34.058479, -118.237534], [39.74691, -105.004723], [39.74435, -105.00943], [39.76627, -104.999107], [40.061871, -104.654373], [34.058441, -118.237549], [34.068748, -118.22921], [41.893082, -87.623756], [36.113411, -115.173218], ] 
    coord = [lat, lon] 
    for coord_city in coord_city_arr: 
        if geopy.distance.geodesic(coord, coord_city).miles < 3: 
            return 1 
        
    return 0


def get_tz_info(first_lat_lon):
    try:
        temp_first_tz = obj.timezone_at(lng=first_lat_lon[-1], lat=first_lat_lon[0])
        if "Indiana" in temp_first_tz:
            temp_first_tz = 'America/New_York'
        
        return temp_first_tz
    except Exception as ex:
        print("TZ cannot be fetched! Why?????")
        print(str(ex))
        return None
       

def remove_values(lst, val):
    new_list = []
    for l in lst:
        if l < val:
            new_list.append(l)
    return new_list

def get_nuttcp_data_length(data):
    count = 0
    for d in data:
        if '0.50 sec = ' in d:
            count+=1 
    return count

def get_start_end_indices(df, start_time, end_time, server_ip):
    # Get the index where the timestamp is greater than or equal to the start_time
    if len(df[df['Timestamp'] >= start_time]) == 0 or len(df[df['Timestamp'] <= end_time]) == 0:
        return pd.DataFrame()
    start_index = df[df['Timestamp'] >= start_time].index[0]

    # Get the index where the timestamp is less than or equal to the end_time
    end_index = df[df['Timestamp'] <= end_time].index[-1]


    # if server_ip != '54.176.53.206' and server_ip != '54.197.223.49' and server_ip != None:
    #     server_type = 'wl'
    # else:
    #     server_type = 'cloud'
        
    temp_df = df[start_index:end_index]
    temp_df['Server Type'] = server_ip
    return temp_df

process_xput_data = 0
process_ping_data = 0
parse_and_plot = 1
if process_xput_data:
    if 1:
        main_op_link_dict = {"verizon" : {"dl" : 0, "ul" : 0}, "tmobile" : {"dl" : 0, "ul" : 0}, "att" : {"dl" : 0, "ul" : 0}}
        main_op_link_simulation_dict = {"verizon" : {"dl" : 0, "ul" : 0}, "tmobile" : {"dl" : 0, "ul" : 0}, "att" : {"dl" : 0, "ul" : 0}}
        for op in ["verizon", "tmobile", "att"]:
            print("######################################################################")
            print("Processing operator: %s" %op)
            if 1:
                print("Generating the times of tests!")
                drive_trip_data_path = "../raw_data/xcal_lte_5g_kpi_data/"
                downlink_df_list = []
                uplink_df_list = []
                for day in ['day_1', 'day_2', 'day_3', 'day_4', 'day_5', 'day_6', 'day_7', 'day_8']:
                    print("Day: %s" %day)
                    if op == 'att':
                        template_data = glob.glob(drive_trip_data_path + "*%s*%s*xlsx" %('atnt', day))
                    else:
                        template_data = glob.glob(drive_trip_data_path + "*%s*%s*xlsx" %(op, day))
                    for template_csv in template_data:
                        df_template = pd.read_excel(template_csv)

                        df_template.drop(df_template.tail(8).index,inplace=True)
                        df_template['TIME_STAMP'] = df_template['TIME_STAMP'].apply(datetime_to_timestamp)
                        df_template = df_template.rename(columns={'TIME_STAMP' : 'Timestamp'})
                        df_template = df_template.sort_values("Timestamp").reset_index(drop=True)

                        # load mimo df and merge UL data to the existing df 
                        if op == 'att':
                            mimo_df = pd.read_excel('../raw_data/mimo_ca_los_bos/%s_%s.xlsx' %('atnt', day))
                        else:
                            mimo_df = pd.read_excel('../raw_data/mimo_ca_los_bos/%s_%s.xlsx' %(op, day))
                        mimo_df.drop(mimo_df.tail(8).index,inplace=True)
                        mimo_df['TIME_STAMP'] = mimo_df['TIME_STAMP'].apply(datetime_to_timestamp)
                        ul_scell_columns = ['TIME_STAMP']
                        ul_scell_columns.extend([i for i in list(mimo_df.columns) if 'UL' in i and 'SCell' in i and '5G' in i])
                        mimo_df = mimo_df[ul_scell_columns]
                        mimo_df = mimo_df.rename(columns={'TIME_STAMP' : 'Timestamp'})
                        df_template = pd.merge(df_template, mimo_df, on='Timestamp')
                        
                        # get app times 
                        app_base = "../raw_data/xcal_lte_5g_kpi_data/app_data_all/%s/2024110%s" %(op, day.split("_")[-1])
                        app_folders = sorted(glob.glob(app_base + "/*"))

                        downlink_start_end_times = []
                        downlink_server_list = []
                        uplink_start_end_times = []
                        uplink_server_list = []
                        for app_folder in app_folders:
                            if '.log' in app_folder:
                                continue 
                            
                            dl_temp_times = []
                            ul_temp_times = []
                            server_ip_list = []
                            app_data_logs = sorted(glob.glob(app_folder + "/*.out"))
                            for app_data in app_data_logs:
                                if 'downlink' in app_data:
                                    fh = open(app_data, "r")
                                    data = fh.readlines()
                                    if day in ['day_1', 'day_2']:
                                        start = (int(data[0].split(":")[-1].strip()) - 3600000) / 1000      
                                        end = start + (get_nuttcp_data_length(data)) * 0.5    

                                    else: 
                                        start = int(data[0].split(":")[-1].strip()) / 1000     
                                        end = start + (get_nuttcp_data_length(data)) * 0.5    
                                        # end = start + 120
                                    fh.close()
                                    dl_temp_times.extend([start, end])
                                    if len(data) > 0:
                                        try:
                                            server_ip = [i for i in data if 'connect to' in i][0].split()
                                            server_ip = server_ip[server_ip.index('with') - 1]
                                            server_ip_list.append(server_ip)
                                        except:
                                            pass

                                elif 'uplink' in app_data:
                                    fh = open(app_data, "r")
                                    data = fh.readlines()
                                    if day in ['day_1', 'day_2']:
                                        start = (int(data[0].split(":")[-1].strip()) - 3600000  ) / 1000          
                                        end = start + (get_nuttcp_data_length(data)) * 0.5    

                                    else: 
                                        start = int(data[0].split(":")[-1].strip()) / 1000     
                                        end = start + (get_nuttcp_data_length(data)) * 0.5    

                                    fh.close()
                                    ul_temp_times.extend([start, end])

                                    if len(data) > 0:
                                        try:
                                            server_ip = [i for i in data if 'connect to' in i][0].split()
                                            server_ip = server_ip[server_ip.index('with') - 1]
                                            server_ip_list.append(server_ip)
                                        except:
                                            pass

                            if len(server_ip_list) > 0:
                                server_ip_list = Counter(server_ip_list).most_common(1)[0][0]
                            else:
                                server_ip_list = 'cloud'
                            dl_temp_times = sorted(dl_temp_times)
                            downlink_start_end_times.append((dl_temp_times[0], dl_temp_times[1]))
                            downlink_server_list.append(server_ip_list)
                            ul_temp_times = sorted(ul_temp_times)
                            try:
                                uplink_start_end_times.append((ul_temp_times[0], ul_temp_times[1]))
                                uplink_server_list.append(server_ip_list)
                            except:
                                # no uplink
                                pass 

                        # work with downlink first
                        print("Processing df_template: %s" %template_csv)
                        for start_end_time, server_ip in zip(downlink_start_end_times, downlink_server_list):
                        # for start_end_time in downlink_start_end_times:
                            start_time, end_time = start_end_time
                            downlink_df_list.append(get_start_end_indices(df_template, start_time, end_time, server_ip))
                            # downlink_df_list.append(get_start_end_indices(df_template, start_time, end_time))

                        for start_end_time, server_ip in zip(uplink_start_end_times, uplink_server_list):
                        # for start_end_time in uplink_start_end_times:
                            start_time, end_time = start_end_time
                            uplink_df_list.append(get_start_end_indices(df_template, start_time, end_time, server_ip))
                            # uplink_df_list.append(get_start_end_indices(df_template, start_time, end_time))


                fh = open('../pkls/performance/2024_op_df_list/with_server/%s_dl.pkl' %op, 'wb')
                pkl.dump(downlink_df_list, fh)
                fh.close()   

                fh = open('../pkls/performance/2024_op_df_list/with_server/%s_ul.pkl' %op, 'wb')
                pkl.dump(uplink_df_list, fh)
                fh.close()
            else:
                print("Loading pickles for operator: %s" %op)
                fh = open('../pkls/performance/2024_op_df_list/with_server/%s_dl.pkl' %op, 'rb')
                downlink_df_list = pkl.load(fh)
                fh.close()   

                fh = open('../pkls/performance/2024_op_df_list/with_server/%s_ul.pkl' %op, 'rb')
                uplink_df_list = pkl.load(fh)
                fh.close()

            diff_list = []
            time_diff_list = []
            for link in ["dl", "ul"]:
                tput_list = []
                df_list_for_simulation = []
                total_distance = 0 
                tput_tech_dist = {"LTE" : 0, "LTE-A" : 0, "5G-low" : 0, "5G-sub6" : 0, "5G-mmWave 28 GHz" : 0, "5G-mmWave 39 GHz" : 0}
                tput_tech_dict = {"LTE" : [], "LTE-A" : [], "5G-low" : [], "5G-sub6" : [], "5G-mmWave 28 GHz" : [], "5G-mmWave 39 GHz" : []}
                wl_cloud_tput_dict = {'wl' : {"LTE" : [], "LTE-A" : [], "5G-low" : [], "5G-sub6" : [], "5G-mmWave 28 GHz" : [], "5G-mmWave 39 GHz" : []}, 'cloud' : {"LTE" : [], "LTE-A" : [], "5G-low" : [], "5G-sub6" : [], "5G-mmWave 28 GHz" : [], "5G-mmWave 39 GHz" : []}}
                tput_tz_tech_dict = {'America/Los_Angeles' : [], 'America/Denver' : [], 'America/Chicago' : [], 'America/New_York' : [], 'America/Phoenix' : [], None : []}

                color_dict = {"LTE" : "#08710C", "LTE-A" : "#70CA32", "5G-low" : "#F3FF33", "5G-sub6" : "#FFB233", "5G-mmWave 28 GHz" : "#FF4629", "5G-mmWave 39 GHz" : "#CB0404" }
                if link == "dl":
                    df_xput_list = downlink_df_list.copy()
                else:
                    df_xput_list = uplink_df_list.copy()
                for df_short in df_xput_list:
                    if len(df_short) == 0:
                        continue
                    df_short.rename(columns={'Timestamp': 'TIME_STAMP'}, inplace=True)
                    df_short_ho = df_short[df_short['Event 5G-NR/LTE Events'].notna()]
                    # if len(df_short_ho) != 0 and op == 'verizon':
                    df_short_ho = df_short[df_short['Event 5G-NR/LTE Events'].str.contains("Handover Success") | df_short['Event 5G-NR/LTE Events'].str.contains("NR SCG Addition Success") | df_short['Event 5G-NR/LTE Events'].str.contains("NR SCG Modification Success")]
                    df_merged = pd.concat([df_short, df_short_ho])
                    df_merged = df_merged.sort_values(by=["TIME_STAMP"])
                    df_merged.reset_index(inplace=True)
                    if len(df_merged) == 0:
                        continue

                    start_area_df_time = df_merged.TIME_STAMP.iloc[0] - 3600
                    end_area_df_time = df_merged.TIME_STAMP.iloc[-1]
                    df_area = pd.read_csv('../raw_data/bos_la_weather_area/data/area.csv')
                    df_area = df_area[(df_area['utc_ts'] >= start_area_df_time) & (df_area['utc_ts'] <= end_area_df_time)]
                    df_area = df_area.rename(columns={'utc_ts' : 'TIME_STAMP'})
                    x = pd.concat([df_merged, df_area])
                    x = x.sort_values(by=["TIME_STAMP"]) 
                    x['value'] = x['value'].ffill()
                    x['value'] = x['value'].fillna(0)
                    break_list = []
                    event = -99
                    start_flag = 0
                    tech_list_all = []
                    for index, row in df_merged.iterrows():
                        if start_flag == 0:
                            # first entry
                            # check if event is empty or not
                            if pd.isnull(row['Event 5G-NR/LTE Events']):
                                event = 0
                                start_flag = 1
                                start_index_count = 0 
                                end_index_count = 0 
                            else:
                                #first entry is event
                                event = 1
                                start_flag = 1
                        else:
                            #row scan in progress 
                            if event == 0 and pd.isnull(row['Event 5G-NR/LTE Events']):
                                #keep increasing index count
                                end_index_count+=1
                            elif event == 0 and pd.notnull(row['Event 5G-NR/LTE Events']):
                                # set event to 1 : new event started
                                event = 1
                                # add truncated df to break list
                                break_list.append(df_merged[start_index_count:end_index_count+1])
                            elif event == 1 and pd.notnull(row['Event 5G-NR/LTE Events']):
                                # continue with event
                                continue
                            elif event == 1 and pd.isnull(row['Event 5G-NR/LTE Events']):
                                # event stopped and throughput started
                                # set event to 0
                                # set start and end index count to current index + 1
                                event = 0
                                start_index_count = index
                                end_index_count = index
                    
                    if event == 0:
                        # add the last throughput value
                        break_list.append(df_merged[start_index_count:end_index_count+1])
                    # now calculate technology - throughput
                    issue_count = 0
                    used_test_count = 0
                    modified_df = []
                    for tput_df in break_list:
                        modified_tech = None
                        # check if 5G frequency or 5G PCI  is empty
                        if len(list(tput_df["5G KPI PCell RF Frequency [MHz]"].dropna())) > 0 or len(list(tput_df["5G KPI PCell RF Serving PCI"].dropna())) > 0:
                            # it is a 5G run 
                            # get type of 5G 
                            freq_list = list(tput_df["5G KPI PCell RF Frequency [MHz]"].dropna())
                            ffreq = float(max(set(freq_list), key=freq_list.count))
                            if int(ffreq) < 1000:
                                modified_tech = "5G-low"
                            elif int(ffreq) > 1000 and int(ffreq) < 7000:
                                modified_tech = "5G-sub6"
                            elif int(ffreq) > 7000 and int(ffreq) < 35000:
                                modified_tech = "5G-mmWave 28 GHz"
                            elif int(ffreq) > 35000:
                                modified_tech = "5G-mmWave 39 GHz"
                        else:
                            # it is LTE
                            # what frequency ? 
                            earfcn_list = list(tput_df["LTE KPI PCell Serving EARFCN(DL)"].dropna())
                            if len(earfcn_list) == 0:
                                continue
                            lfreq = earfcn_to_freq(int(max(set(earfcn_list), key=earfcn_list.count)))

                            if int(lfreq) < 1000:
                                modified_tech = "LTE"
                            elif int(lfreq) > 1000:
                                modified_tech = "LTE-A"

                        if link == 'dl':
                            temp_df = tput_df[['TIME_STAMP', 'Lat', 'Lon', "Smart Phone Smart Throughput Mobile Network DL Throughput [Mbps]", "Server Type"]]
                            temp_df = temp_df.dropna(subset=["Smart Phone Smart Throughput Mobile Network DL Throughput [Mbps]"])
                            xput_list = list(temp_df["Smart Phone Smart Throughput Mobile Network DL Throughput [Mbps]"])
                        else:
                            temp_df = tput_df[['TIME_STAMP', 'Lat', 'Lon', "Smart Phone Smart Throughput Mobile Network UL Throughput [Mbps]", "Server Type"]]
                            temp_df = temp_df.dropna(subset=["Smart Phone Smart Throughput Mobile Network UL Throughput [Mbps]"])
                            xput_list = list(temp_df["Smart Phone Smart Throughput Mobile Network UL Throughput [Mbps]"])

                        tput_list.extend(xput_list)
                        tput_tech_dict[modified_tech].extend(xput_list)
                        is_wavelength = 'cloud'
                        tz = None
                        if len(temp_df['Server Type'].dropna()) > 0:
                            server_ip = Counter(temp_df['Server Type'].dropna()).most_common(1)[0][0]
                            if server_ip != '54.176.53.206' and server_ip != '54.197.223.49' and server_ip != None:
                                is_wavelength = 'wl'
                            else:
                                is_wavelength = 'cloud'
                            if pd.isnull(temp_df.iloc[0]['Lat']) or pd.isnull(temp_df.iloc[0]['Lon']):
                                tz = None
                            else:
                                tz = get_tz_info((temp_df.iloc[0]['Lat'], temp_df.iloc[0]['Lon']))
                                
                        wl_cloud_tput_dict[is_wavelength][modified_tech].extend(xput_list)
                        tput_tz_tech_dict[tz].extend(xput_list)

                        if len(temp_df) > 1:
                            # calculate distance +
                            lat_list = list(temp_df['Lat'].dropna())
                            lon_list = list(temp_df['Lon'].dropna())

                            prev_lat = lat_list[0]
                            prev_lon = lon_list[0]

                            for lat, lon in zip(lat_list, lon_list):
                                total_distance += geopy.distance.geodesic((prev_lat, prev_lon), (lat, lon)).miles
                                tput_tech_dist[modified_tech] += geopy.distance.geodesic((prev_lat, prev_lon), (lat, lon)).miles
                                prev_lat = lat
                                prev_lon = lon

                        temp_df['Technology'] = [modified_tech] * len(temp_df)
                        modified_df.append(temp_df)
                        modified_tech = None

                    if len(modified_df) > 0:
                        df_list_for_simulation.append(pd.concat(modified_df))

                main_op_link_dict[op][link] = [tput_list, tput_tech_dict, wl_cloud_tput_dict, tput_tz_tech_dict, total_distance, tput_tech_dist]
                main_op_link_simulation_dict[op][link] = df_list_for_simulation.copy()

        filehandler = open("../pkls/performance/2024_op_df_list/with_server/processed/main_op_link_dict.pkl", "wb")
        pkl.dump(main_op_link_dict, filehandler)
        filehandler.close()

        filehandler = open("../pkls/performance/2024_op_df_list/with_server/processed/main_op_link_simulation_dict.pkl", "wb")
        pkl.dump(main_op_link_simulation_dict, filehandler)
        filehandler.close()

    else:
        filehandler = open('../pkls/performance/2024_op_df_list/with_server/processed/main_op_link_dict.pkl', "rb")
        main_op_link_dict = pkl.load(filehandler)
        filehandler.close()

        if 1:
            label_dict = {'LTE' : 'LTE', 'LTE-A' : 'LTE-A', '5G-low' : '5G-low', '5G-sub6' : '5G-mid', '5G-mmWave 28 GHz' : '5G-mmWave 28 GHz', '5G-mmWave 39 GHz' : '5G-mmWave 39 GHz'}
            color_dict = {"LTE" : "#08710C", "LTE-A" : "#70CA32", "5G-low" : "#F3FF33", "5G-sub6" : "#FFB233", "5G-mmWave 28 GHz" : "#FF4629", "5G-mmWave 39 GHz" : "#CB0404" }
            fig, ax = plt.subplots(1, 2, figsize=(7,5.5), sharey=True)
            op_list_mod = ["Verizon", "T-Mobile", "AT&T"]
            i = 0
            for link in ["dl", "ul"]:
                tech_percent_dict = {"verizon" : [], "tmobile" : [], "att" : []}
                tech_values_dict = {"verizon" : [], "tmobile" : [], "att" : []}
                for op in ["verizon", "tmobile", "att"]:
                    total_distance = main_op_link_dict[op][link][4]
                    tput_tech_dist = main_op_link_dict[op][link][5]
                    dummy_tech_dict = tput_tech_dist.copy()
                    for tech in dummy_tech_dict.keys():
                        dummy_tech_dict[tech] = round((tput_tech_dist[tech]/total_distance) * 100,4)
                    tech_percent_dict[op] = dummy_tech_dict

                op_list = ["verizon", "tmobile", "att"]
                tech_percent_dict_graph = {'LTE' : [] , 'LTE-A' : [], '5G-low' : [], '5G-sub6' : [], '5G-mmWave 28 GHz' : [], '5G-mmWave 39 GHz' : []}
                for tech in tech_percent_dict_graph.keys():
                    for op in op_list:
                        tech_percent_dict_graph[tech].append(tech_percent_dict[op][tech])

                width=0.35
                ax[i].bar(op_list_mod, tech_percent_dict_graph['LTE'], width, color=color_dict["LTE"], label="LTE")
                prev = tech_percent_dict_graph['LTE']
                for tech in ['LTE-A', '5G-low', '5G-sub6', '5G-mmWave 28 GHz', '5G-mmWave 39 GHz']:
                    ax[i].bar(op_list_mod, tech_percent_dict_graph[tech], width, color=color_dict[tech], bottom=prev, label=label_dict[tech])
                    prev = list( map(add, prev, tech_percent_dict_graph[tech]))
                i+=1
            # ax[0].set_ylabel("Percentage coverage per mile (%)")
            ax[0].set_ylim(0, 120)
            # ax[0].legend(ncol=2, loc="upper left", fontsize=9.5)
            ax[0].set_title("Downlink", fontweight="bold", fontsize=15)
            ax[1].set_title("Uplink", fontweight="bold", fontsize=15)
            ax[0].set_yticks([0, 20, 40, 60, 80, 100])
            plt.tight_layout()
            plt.savefig("../plots/coverage/fig_2b.pdf")
            plt.close()
            print()

        for op in main_op_link_dict.keys():
            for link in main_op_link_dict[op].keys():
                wl_cloud_tput_dict = main_op_link_dict[op][link][2]

                print("Operator: %s, Link: %s" %(op, link))
                for key in wl_cloud_tput_dict.keys():
                    for tech in wl_cloud_tput_dict[key].keys():
                        x = [i for i in wl_cloud_tput_dict[key][tech] if not pd.isnull(i)]
                        print("%s, %s Median throughput: %f (%d)" %(tech, key, np.median(x), len(x)))

# icmp ping process
if process_ping_data:
    base = "../pkls/performance/2024_op_df_list/ping/"
    main_op_link_dict = {'verizon' : [], 'tmobile' : [], 'atnt' : []}
    for op in ['verizon', 'tmobile', 'atnt']:
        fh = open(base + "rtt_break_%s.pkl" %op, 'rb')
        ping_df_list = pkl.load(fh)
        fh.close()

        rtt_list = []
        rtt_tech_dict = {"LTE" : [], "LTE-A" : [], "5G-low" : [], "5G-sub6" : [], "5G-mmWave 28 GHz" : [], "5G-mmWave 39 GHz" : []}
        wl_cloud_rtt_dict = {'wl' : {"LTE" : [], "LTE-A" : [], "5G-low" : [], "5G-sub6" : [], "5G-mmWave 28 GHz" : [], "5G-mmWave 39 GHz" : []}, 'cloud' : {"LTE" : [], "LTE-A" : [], "5G-low" : [], "5G-sub6" : [], "5G-mmWave 28 GHz" : [], "5G-mmWave 39 GHz" : []}}
        downtown_rtt_dict = {"LTE" : [], "LTE-A" : [], "5G-low" : [], "5G-sub6" : [], "5G-mmWave 28 GHz" : [], "5G-mmWave 39 GHz" : []}
        non_downtown_rtt_dict = {"LTE" : [], "LTE-A" : [], "5G-low" : [], "5G-sub6" : [], "5G-mmWave 28 GHz" : [], "5G-mmWave 39 GHz" : []}
        tz_rtt_dict = {'America/Los_Angeles' : {'wl' : {"LTE" : [], "LTE-A" : [], "5G-low" : [], "5G-sub6" : [], "5G-mmWave 28 GHz" : [], "5G-mmWave 39 GHz" : []}, 'cloud' : {"LTE" : [], "LTE-A" : [], "5G-low" : [], "5G-sub6" : [], "5G-mmWave 28 GHz" : [], "5G-mmWave 39 GHz" : []}}, 'America/Denver' : {'wl' : {"LTE" : [], "LTE-A" : [], "5G-low" : [], "5G-sub6" : [], "5G-mmWave 28 GHz" : [], "5G-mmWave 39 GHz" : []}, 'cloud' : {"LTE" : [], "LTE-A" : [], "5G-low" : [], "5G-sub6" : [], "5G-mmWave 28 GHz" : [], "5G-mmWave 39 GHz" : []}}, 'America/Chicago' : {'wl' : {"LTE" : [], "LTE-A" : [], "5G-low" : [], "5G-sub6" : [], "5G-mmWave 28 GHz" : [], "5G-mmWave 39 GHz" : []}, 'cloud' : {"LTE" : [], "LTE-A" : [], "5G-low" : [], "5G-sub6" : [], "5G-mmWave 28 GHz" : [], "5G-mmWave 39 GHz" : []}}, 'America/New_York' : {'wl' : {"LTE" : [], "LTE-A" : [], "5G-low" : [], "5G-sub6" : [], "5G-mmWave 28 GHz" : [], "5G-mmWave 39 GHz" : []}, 'cloud' : {"LTE" : [], "LTE-A" : [], "5G-low" : [], "5G-sub6" : [], "5G-mmWave 28 GHz" : [], "5G-mmWave 39 GHz" : []}}, 'America/Phoenix' : {'wl' : {"LTE" : [], "LTE-A" : [], "5G-low" : [], "5G-sub6" : [], "5G-mmWave 28 GHz" : [], "5G-mmWave 39 GHz" : []}, 'cloud' : {"LTE" : [], "LTE-A" : [], "5G-low" : [], "5G-sub6" : [], "5G-mmWave 28 GHz" : [], "5G-mmWave 39 GHz" : []}}, None : {'wl' : {"LTE" : [], "LTE-A" : [], "5G-low" : [], "5G-sub6" : [], "5G-mmWave 28 GHz" : [], "5G-mmWave 39 GHz" : []}, 'cloud' : {"LTE" : [], "LTE-A" : [], "5G-low" : [], "5G-sub6" : [], "5G-mmWave 28 GHz" : [], "5G-mmWave 39 GHz" : []}}}

        for df_short in ping_df_list:
            if len(df_short) == 0:
                continue
            
            # df_short = df_short.drop(columns=['Server Type'])
            df_short.rename(columns={'Timestamp': 'TIME_STAMP'}, inplace=True)
            df_short_ho = df_short[df_short['Event 5G-NR/LTE Events'].notna()]
            # if len(df_short_ho) != 0 and op == 'verizon':
            df_short_ho = df_short[df_short['Event 5G-NR/LTE Events'].str.contains("Handover Success") | df_short['Event 5G-NR/LTE Events'].str.contains("NR SCG Addition Success") | df_short['Event 5G-NR/LTE Events'].str.contains("NR SCG Modification Success")]
            df_merged = pd.concat([df_short, df_short_ho])
            df_merged = df_merged.sort_values(by=["TIME_STAMP"])
            df_merged.reset_index(inplace=True)
            if len(df_merged) == 0:
                continue

            break_list = []
            event = -99
            start_flag = 0
            tech_list_all = []
            df_merged['Lat'] = df_merged['Lat'].fillna(method='ffill').fillna(method='bfill')
            df_merged['Lon'] = df_merged['Lon'].fillna(method='ffill').fillna(method='bfill')
            for index, row in df_merged.iterrows(): 
                if start_flag == 0:
                    # first entry
                    # check if event is empty or not
                    if pd.isnull(row['Event 5G-NR/LTE Events']):
                        event = 0
                        start_flag = 1
                        start_index_count = 0 
                        end_index_count = 0 
                    else:
                        #first entry is event
                        event = 1
                        start_flag = 1
                else:
                    #row scan in progress 
                    if event == 0 and pd.isnull(row['Event 5G-NR/LTE Events']):
                        #keep increasing index count
                        end_index_count+=1
                    elif event == 0 and pd.notnull(row['Event 5G-NR/LTE Events']):
                        # set event to 1 : new event started
                        event = 1
                        # add truncated df to break list
                        break_list.append(df_merged[start_index_count:end_index_count+1])
                    elif event == 1 and pd.notnull(row['Event 5G-NR/LTE Events']):
                        # continue with event
                        continue
                    elif event == 1 and pd.isnull(row['Event 5G-NR/LTE Events']):
                        # event stopped and throughput started
                        # set event to 0
                        # set start and end index count to current index + 1
                        event = 0
                        start_index_count = index
                        end_index_count = index
            
            if event == 0:
                # add the last throughput value
                break_list.append(df_merged[start_index_count:end_index_count+1])
            # now calculate technology - throughput
            issue_count = 0
            used_test_count = 0
            for tput_df in break_list:
                modified_tech = None
                # check if 5G frequency or 5G PCI  is empty
                if len(list(tput_df["5G KPI PCell RF Frequency [MHz]"].dropna())) > 0 or len(list(tput_df["5G KPI PCell RF Serving PCI"].dropna())) > 0:
                    # it is a 5G run 
                    # get type of 5G 
                    freq_list = list(tput_df["5G KPI PCell RF Frequency [MHz]"].dropna())
                    ffreq = float(max(set(freq_list), key=freq_list.count))
                    if int(ffreq) < 1000:
                        modified_tech = "5G-low"
                    elif int(ffreq) > 1000 and int(ffreq) < 7000:
                        modified_tech = "5G-sub6"
                    elif int(ffreq) > 7000 and int(ffreq) < 35000:
                        modified_tech = "5G-mmWave 28 GHz"
                    elif int(ffreq) > 35000:
                        modified_tech = "5G-mmWave 39 GHz"
                else:
                    # it is LTE
                    # what frequency ? 
                    earfcn_list = list(tput_df["LTE KPI PCell Serving EARFCN(DL)"].dropna())
                    if len(earfcn_list) == 0:
                        continue
                    lfreq = earfcn_to_freq(int(max(set(earfcn_list), key=earfcn_list.count)))

                    if int(lfreq) < 1000:
                        modified_tech = "LTE"
                    elif int(lfreq) > 1000:
                        modified_tech = "LTE-A"


                temp_df = tput_df[['TIME_STAMP', 'Lat', 'Lon', "ping_data", "Server Type"]]
                temp_df = temp_df.dropna(subset=["ping_data"])
                ping_list = list(temp_df["ping_data"])

                rtt_list.extend(ping_list)
                rtt_tech_dict[modified_tech].extend(ping_list)
                is_wavelength = 'cloud'
                tz = None
                if len(temp_df['Server Type'].dropna()) > 0:
                    server_ip = Counter(temp_df['Server Type'].dropna()).most_common(1)[0][0]
                    if server_ip != '54.176.53.206' and server_ip != '54.197.223.49' and server_ip != None:
                        is_wavelength = 'wl'
                    else:
                        is_wavelength = 'cloud'

                    if pd.isnull(temp_df.iloc[0]['Lat']) or pd.isnull(temp_df.iloc[0]['Lon']):
                        tz = None
                    else:
                        tz = get_tz_info((temp_df.iloc[0]['Lat'], temp_df.iloc[0]['Lon']))

                wl_cloud_rtt_dict[is_wavelength][modified_tech].extend(ping_list)
                tz_rtt_dict[tz][is_wavelength][modified_tech].extend(ping_list)

                if not pd.isnull(tuple(tput_df[['Lat', 'Lon']].dropna().median())[0]):
                    if downtown_measurements_mod(tuple(tput_df[['Lat', 'Lon']].dropna().median())):
                        downtown_rtt_dict[modified_tech].extend(ping_list)
                    else:
                        non_downtown_rtt_dict[modified_tech].extend(ping_list)
                modified_tech = None

        main_op_link_dict[op] = [rtt_list, rtt_tech_dict, wl_cloud_rtt_dict, downtown_rtt_dict, tz_rtt_dict, non_downtown_rtt_dict]

    fh = open("../pkls/performance/2024_op_df_list/ping/processed/main_op_link_dict.pkl", "wb")
    pkl.dump(main_op_link_dict, fh)
    fh.close()

if parse_and_plot:
    filehandler = open('../pkls/performance/2024_op_df_list/with_server/processed/main_op_link_dict.pkl', "rb")
    main_op_link_xput_dict = pkl.load(filehandler)
    main_op_link_xput_dict['atnt'] = main_op_link_xput_dict['att'].copy()
    del(main_op_link_xput_dict['att'])
    filehandler.close()

    if 1:
        # icmp ping
        fh = open("../pkls/performance/2024_op_df_list/ping/processed/main_op_link_dict.pkl", "rb")
        main_op_link_ping_dict = pkl.load(fh)
        fh.close()

    tz_name_dict = {'America/Los_Angeles' : "Pacific Time", 'America/Denver' : "Mountain Time", 'America/Chicago' : "Central Time", 'America/New_York' : "Eastern Time" }    
    tz_color_dict = {'America/Los_Angeles' : "black", 'America/Denver' : "red", 'America/Chicago' : "green", 'America/New_York' : "gold" }    
    color_dict = {'verizon': 'red', 'tmobile': 'magenta', 'atnt': 'blue'}
    label_dict = {'verizon': 'Verizon', 'tmobile': 'T-Mobile', 'atnt': 'AT&T'}
    tech_color_dict = {"LTE" : "#08710C", "LTE-A" : "#70CA32", "5G-low" : "#F3FF33", "5G-sub6" : "#FFB233", "5G-mmWave 28 GHz" : "#FF4629", "5G-mmWave 39 GHz" : "#CB0404" }
    tech_label_dict = {"LTE" : "LTE", "LTE-A" : "LTE-A", "5G-low" : "5G low", "5G-sub6" : "5G mid", "5G-mmWave 28 GHz" : "5G mmWave (28 GHz) ", "5G-mmWave 39 GHz" : "5G mmWave (39 GHz)" }

    # overall xput ping 
    if 1:
        # get starlink data
        if 1:
            starlink_path = "../raw_data/app_data_all/starlink/"
            day_list = glob.glob(starlink_path + "*")
            runwise_starlink_dl_list =  {}
            runwise_starlink_ul_list =  {}
            runwise_starlink_rtt_list = {}

            dl_run_id =  -1
            ul_run_id =  -1
            rtt_run_id = -1

            for day in day_list:
                print("Day: %s" %day)
                run_list = glob.glob(day + "/*")
                for run in run_list:
                    if ".log" in run:
                        continue
                    starlink_dl_list = []
                    starlink_ul_list = []
                    starlink_rtt_list = []
                    dl_file = None 
                    ul_file = None
                    rtt_file = None
                    dl_file_list = sorted(glob.glob(run + "/tcp_downlink_*"))
                    if len(dl_file_list) > 0:
                        dl_file = dl_file_list[0]
                    ul_file_list = sorted(glob.glob(run + "/tcp_uplink_*"))
                    if len(ul_file_list) > 0:
                        ul_file = ul_file_list[0]
                    rtt_file_list = sorted(glob.glob(run + "/icmp_ping_*"))
                    if len(rtt_file_list) > 0:
                        rtt_file = rtt_file_list[0]
                    if dl_file == None and ul_file == None and rtt_file == None:
                        continue

                    if dl_file != None:
                        dl_run_id+=1
                        fh = open(dl_file, 'r')
                        data = fh.readlines()
                        fh.close()
                        for d in data:
                            if '0.50 sec = ' in d:
                                bps_index = -999 
                                for i in d.split():
                                    if 'bps' in i:
                                        bps_index = d.split().index(i)
                                        break
                                if bps_index != -999:
                                    dl_bps = d.split()[bps_index - 1]
                                    if 'Kbps' in d.split()[bps_index]:
                                        dl_bps = float(dl_bps) / 1000
                                    elif 'Mbps' in d.split()[bps_index]:
                                        dl_bps = float(dl_bps)
                                    elif 'Gbps' in d.split()[bps_index]:
                                        dl_bps = float(dl_bps) * 1000
                                    else:
                                        print("WTF! DL!")
                                        sys.exit(1)
                                    starlink_dl_list.append(dl_bps)

                        if dl_run_id == 189:
                            a = 1
                        runwise_starlink_dl_list[dl_run_id] = starlink_dl_list.copy()

                    if ul_file != None:
                        ul_run_id+=1
                        fh = open(ul_file, 'r')
                        data = fh.readlines()
                        fh.close()
                        for d in data:
                            if '0.50 sec = ' in d:
                                bps_index = -999 
                                for i in d.split():
                                    if 'bps' in i:
                                        bps_index = d.split().index(i)
                                        break
                                if bps_index != -999:
                                    ul_bps = d.split()[bps_index - 1]
                                    if 'Kbps' in d.split()[bps_index]:
                                        ul_bps = float(ul_bps) / 1000
                                    elif 'Mbps' in d.split()[bps_index]:
                                        ul_bps = float(ul_bps)
                                    elif 'Gbps' in d.split()[bps_index]:
                                        ul_bps = float(ul_bps) * 1000
                                    else:
                                        print("WTF! UL!")
                                        sys.exit(1)
                                    starlink_ul_list.append(ul_bps)

                        runwise_starlink_ul_list[ul_run_id] = starlink_ul_list.copy()

                    if rtt_file != None:
                        rtt_run_id+=1
                        fh = open(rtt_file, 'r')
                        data = fh.readlines()
                        fh.close()
                        for d in data:
                            if 'icmp_seq=' in d and 'ttl=' in d:
                                rtt_index = -999 
                                for i in d.split():
                                    if 'ms' in i:
                                        rtt_index = d.split().index(i)
                                        break
                                if rtt_index != -999:
                                    rtt_ms = d.split()[rtt_index - 1]
                                    starlink_rtt_list.append(float(rtt_ms.split("=")[-1]))

                        runwise_starlink_rtt_list[rtt_run_id] = starlink_rtt_list.copy()
            
        flattened_dl_list = [elem for item in runwise_starlink_dl_list  .values() for elem in item ]
        flattened_ul_list = [elem for item in runwise_starlink_ul_list  .values() for elem in item ]
        flattened_rtt_list = [elem for item in runwise_starlink_rtt_list.values() for elem in item ]
    
        if 1:
            xlabels = {'dl': 'DL Throughput (Mbps)', 'ul': 'UL Throughput (Mbps)', 'ping': 'RTT (ms)'}
            xlims = {'dl': 3500, 'ul': 350, 'ping': 165}
            link_to_axis = {'dl': 0, 'ul': 1, 'ping': 2}
            fig, ax = plt.subplots(1, 3, figsize=(12, 4), sharey=True)

            inset_xlim_map = {'dl': (0, 350), 'ul': (0, 50), 'ping': (0, 100)}
            # Main plotting loop
            for link in ['dl', 'ul', 'ping']:
                axis_idx = link_to_axis[link]
                for op in color_dict.keys():
                    if link == 'ping':
                        data = np.sort(main_op_link_ping_dict[op][0])
                    else:
                        data = np.sort(main_op_link_xput_dict[op][link][0])

                    # print("Operator: %s, Link: %s -- (%s/%s/%s)" %(op, link, str(round(np.quantile(data, 0.1))), str(round(np.quantile(data, 0.5))), str(round(np.quantile(data, 0.75)))))
                    cdf = np.linspace(0, 1, data.size)
                    ax[axis_idx].plot(data, cdf, label=label_dict[op], color=color_dict[op])

                ax[axis_idx].set_xlabel(xlabels[link])
                ax[axis_idx].set_xlim(0, xlims[link])
                ax[axis_idx].set_ylim(0, 1)
                ax[axis_idx].grid(True)

                # Add inset showing zoomed-in region with all operators
                if link != 'ping':
                    inset = inset_axes(ax[axis_idx], width="45%", height="45%", loc='upper right')

                for op in color_dict.keys():
                    if link == 'ping':
                        data = np.sort(main_op_link_ping_dict[op][0])
                    else:
                        data = np.sort(main_op_link_xput_dict[op][link][0])
                    cdf = np.linspace(0, 1, data.size)
                    if link != 'ping':
                        inset.plot(data, cdf, color=color_dict[op])

                if link != 'ping':
                    inset.set_xlim(*inset_xlim_map[link])
                    inset.set_ylim(0, 1)
                    inset.tick_params(labelsize=13)
                    inset.grid(True)

            # Shared settings
            ax[0].set_ylabel("CDF")
            ax[1].legend(loc='lower right')
            plt.tight_layout()
            plt.savefig('../plots/performance/overall_performance_cdf.pdf')
            plt.close()
            a = 1

        # overall with starlink
        if 1:
            xlabels = {'dl': 'DL Throughput (Mbps)', 'ul': 'UL Throughput (Mbps)', 'ping': 'RTT (ms)'}
            xlims = {'dl': 3500, 'ul': 350, 'ping': 165}
            link_to_axis = {'dl': 0, 'ul': 1, 'ping': 2}
            color_dict = {'verizon': 'red', 'tmobile': 'magenta', 'atnt': 'blue', 'starlink': 'black'}
            label_dict = {'verizon': 'Verizon', 'tmobile': 'T-Mobile', 'atnt': 'AT&T', 'starlink': 'Starlink'}

            fig, ax = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
            inset_xlim_map = {'dl': (0, 350), 'ul': (0, 50), 'ping': (0, 100)}
            # Main plotting loop
            for link in ['dl', 'ul', 'ping']:
                axis_idx = link_to_axis[link]
                for op in color_dict.keys():
                    if op == 'starlink':
                        if link == 'ping':
                            data = np.sort(flattened_rtt_list)
                        elif link == 'dl':
                            data = np.sort(flattened_dl_list)
                        else:
                            data = np.sort(flattened_ul_list)
                    else:
                        if link == 'ping':
                            data = np.sort(main_op_link_ping_dict[op][0])
                        else:
                            data = np.sort(main_op_link_xput_dict[op][link][0])

                    # print("Operator: %s, Link: %s -- (%s/%s/%s)" %(op, link, str(round(np.quantile(data, 0.25))), str(round(np.quantile(data, 0.5))), str(round(np.quantile(data, 0.75)))))
                    cdf = np.linspace(0, 1, data.size)
                    ax[axis_idx].plot(data, cdf, label=label_dict[op], color=color_dict[op])

                ax[axis_idx].set_xlabel(xlabels[link])
                ax[axis_idx].set_xlim(0, xlims[link])
                ax[axis_idx].set_ylim(0, 1)
                ax[axis_idx].grid(True)

                # Add inset showing zoomed-in region with all operators
                if link != 'ping':
                    # inset = inset_axes(ax[axis_idx], width="45%", height="45%", loc='lower right')
                # else:
                    inset = inset_axes(ax[axis_idx], width="45%", height="45%", loc='upper right')

                for op in color_dict.keys():
                    if op == 'starlink':
                        if link == 'ping':
                            data = np.sort(flattened_rtt_list)
                        elif link == 'dl':
                            data = np.sort(flattened_dl_list)
                        else:
                            data = np.sort(flattened_ul_list)
                    else:
                        if link == 'ping':
                            data = np.sort(main_op_link_ping_dict[op][0])
                        else:
                            data = np.sort(main_op_link_xput_dict[op][link][0])
                    cdf = np.linspace(0, 1, data.size)
                    if link != 'ping':
                        inset.plot(data, cdf, color=color_dict[op])

                if link != 'ping':
                    inset.set_xlim(*inset_xlim_map[link])
                    inset.set_ylim(0, 1)
                    inset.tick_params(labelsize=13)
                    inset.grid(True)

            # Shared settings
            ax[0].set_ylabel("CDF")
            ax[2].legend(loc='lower right')
            plt.tight_layout()
            plt.savefig('../plots/performance/overall_performance_with_starlink_cdf.pdf')
            plt.close()