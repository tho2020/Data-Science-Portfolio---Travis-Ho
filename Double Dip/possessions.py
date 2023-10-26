import pandas as pd
import matplotlib.pyplot as plt
import statistics as stat

def load_drives():
    #Loading dataframe
    df = pd.read_csv(r'toss_up_v2.csv')
    pd.set_option('display.max_columns', None)
    df = df.replace(["PUNT","FUMBLE","END OF HALF","INTERCEPTION",
                             "DOWNS","END OF GAME","MISSED FG"],int(0))
    df = df.replace(["FIELD GOAL"],int(3))
    df = df.replace(["TOUCHDOWN"],int(6))
    df = df.replace(["SAFETY"],int(-2))
    df = df.replace(["INTERCEPTION-TD","FUMBLE-TD"],int(-6))
    df = df.astype({"second_last_drive_end_event_q2" : int,
                    "last_drive_end_event_q2" : int, 
                    "next_drive_end_event_q3" : int})
    return df

def total_points(drives):
    #Summing total points from all drives
    cols = ["last_drive_end_event_q2",
            "next_drive_end_event_q3"]
    drives["points"] = drives[cols].sum(axis=1)
    return drives

def new_field_pos(drives):
    #changing field position to yards to go
    columns = ["second_last_drive_q2_start_field_position",
               "last_drive_q2_start_field_position",
               "next_drive_q3_start_field_position"]
    for column in columns:
        drives[column] = drives[column].apply(lambda x: x + 100 if x < 0 else x)
    
    return drives
    
def total_epa(drives):
    #Summing EPA for drives
    cols = ["last_drive_q2_expected_points",
            "next_drive_expected_points"]
    drives["epa_sum"] = drives[cols].sum(axis=1)
    return drives

def convert_times(drives):
    #convert time from second to last drive q2
    new_time_list1 = []
    minute_list1 = []
    second_list1 = []
    total_time1 = []
    for time in drives["second_last_drive_q2_clock"]:
        new_time = time.split(':')
        new_time_list1.append(new_time)
    for item in new_time_list1:
        minute = int(item[0])
        convert_seconds = minute * 60
        minute_list1.append(convert_seconds)
        second = int(item[1])
        second_list1.append(second)
    for i, j in zip(minute_list1, second_list1):
        new_time = i + j
        total_time1.append(new_time)

    #convert time from last drive q2
    new_time_list2 = []
    minute_list2 = []
    second_list2 = []
    total_time2 = []
    for time in drives["last_drive_q2_clock"]:
        new_time = time.split(':')
        new_time_list2.append(new_time)
    for item in new_time_list2:
        minute = int(item[0])
        convert_seconds = minute * 60
        minute_list2.append(convert_seconds)
        second = int(item[1])
        second_list2.append(second)
    for i, j in zip(minute_list2, second_list2):
        new_time = i + j
        total_time2.append(new_time)
        
    #convert time from first drive q3    
    new_time_list3 = []
    minute_list3 = []
    second_list3 = []
    total_time3 = []
    for time in drives["next_drive_q3_clock"]:
        new_time = time.split(':')
        new_time_list3.append(new_time)
    for item in new_time_list3:
        minute = int(item[0])
        convert_seconds = minute * 60
        minute_list3.append(convert_seconds)
        second = int(item[1])
        second_list3.append(second)
    for i, j in zip(minute_list3, second_list3):
        new_time = i + j
        total_time3.append(new_time)
    
    #Add to dataframe
    drives["second_last_q2_secs"] = total_time1
    drives["last_q2_secs"] = total_time2
    drives["first_q3_secs"] = total_time3

    return drives

def coup(drives):
    #Coupling games by GameID
    data_dict = {}
    
    for ind in drives.index:
        game_id = drives.loc[ind, "game_id"]
        if game_id not in data_dict:
            data_dict[game_id] = [drives.loc[ind].to_dict()]
        else:
            data_dict[game_id].append(drives.loc[ind].to_dict())
    
    return data_dict

def dubdip(drives_dict, game_id=None):
    #Getting all double dip games
    if game_id is not None:
        if game_id not in drives_dict:
            print(f"Game ID {game_id} not found in the dictionary.")
            return

        data_for_game_id = drives_dict[game_id]
        double_dip = []
        not_double_dip = []
    
        for i in range(len(data_for_game_id) - 1):
            current_dataq2 = data_for_game_id[i]['last_q2_secs']
            next_dataq2 = data_for_game_id[i + 1]['last_q2_secs']
            current_dataq3 = data_for_game_id[i]['first_q3_secs']
            next_dataq3 = data_for_game_id[i + 1]['first_q3_secs']

            if current_dataq2 < next_dataq2 and current_dataq3 > next_dataq3:
                double_dip.append((data_for_game_id[i], data_for_game_id[i+1]))
            if current_dataq2 > next_dataq2 and current_dataq3 < next_dataq3:
                double_dip.append((data_for_game_id[i], data_for_game_id[i+1]))
            else:
                not_double_dip.append((data_for_game_id[i], data_for_game_id[i+1]))
        
        return double_dip
    
    else:
        double_dip = []
        for game_id in drives_dict:
            double_dip_data = dubdip(drives_dict, game_id)
            if double_dip_data:
                double_dip.extend(double_dip_data)

        return double_dip
        
def length_drive(double_dip):
    drive_length_list = []
    opp_final_drive_list = []
    get_ball_list = []
    opp_get_ball_list = []

    for index in range(len(double_dip)):
        first_team = double_dip[index][0]
        second_team = double_dip[index][1]

        first_team_second_last_q2_secs = first_team['second_last_q2_secs']
        first_team_last_q2_secs = first_team['last_q2_secs']
        second_team_second_last_q2_secs = second_team['second_last_q2_secs']
        second_team_last_q2_secs = second_team['last_q2_secs']

        if first_team_last_q2_secs < second_team_last_q2_secs:
            drive_length = first_team_second_last_q2_secs - second_team_last_q2_secs
            opp_drive_length = second_team_last_q2_secs - first_team_last_q2_secs
            get_ball = first_team_second_last_q2_secs
            opp_get_ball = second_team_last_q2_secs
            drive_length_list.append(drive_length)
            opp_final_drive_list.append(opp_drive_length)
            get_ball_list.append(get_ball)
            opp_get_ball_list.append(opp_get_ball)
        elif second_team_last_q2_secs < first_team_last_q2_secs:
            drive_length = second_team_second_last_q2_secs - first_team_last_q2_secs
            opp_drive_length = first_team_last_q2_secs - second_team_last_q2_secs
            get_ball = second_team_second_last_q2_secs
            opp_get_ball = first_team_last_q2_secs
            drive_length_list.append(drive_length)
            opp_final_drive_list.append(opp_drive_length)
            get_ball_list.append(get_ball)
            opp_get_ball_list.append(opp_get_ball)
        
    #Getting rid of negative values created by fumble/int TDs
    for i in drive_length_list:
        if i < 0:
            drive_length_list.remove(i)
    for j in opp_final_drive_list:
        if j < 0:
            opp_final_drive_list.remove(j)

    return drive_length_list, opp_final_drive_list, get_ball_list, opp_get_ball_list


def drive_time_analysis(drive_time):
    drive_time_hist = plt.hist(drive_time, bins=50, edgecolor='black')
    plt.title('Length of Second to Last Drive vs. Double Dip Tendency')
    plt.xlabel('Second to Last Drive Time (Secs)')
    plt.ylabel('Frequency of Double Dip')
    drive_time_df = pd.DataFrame(drive_time)
    drive_time_sumtab = drive_time_df.describe()
    return drive_time_hist, drive_time_sumtab

def opp_drive_time_analysis(opp_drive_time):
    opp_drive_time_hist = plt.hist(opp_drive_time, bins=50, edgecolor='black')
    plt.title('Length of Final Drive of Opponent vs. Double Dip Tendency')
    plt.xlabel('Final Opponent Drive Time (Secs)')
    plt.ylabel('Frequency of Double Dip')
    opp_drive_time_df = pd.DataFrame(opp_drive_time)
    opp_drive_time_sumtab = opp_drive_time_df.describe()
    return opp_drive_time_hist, opp_drive_time_sumtab

def get_ball_analysis(get_ball):
    get_ball_hist = plt.hist(get_ball, bins = 50, edgecolor='black', color='orange')
    plt.title('Time Left on Clock vs. Double Dip Tendency')
    plt.xlabel('Time Left on Clock (Second to Last Drive)')
    plt.ylabel('Frequency of Double Dip')
    mean = stat.mean(get_ball)
    plt.axvline(mean, color='red', linestyle='dashed', linewidth=2, label=f'Mean = {mean}')
    plt.text(mean, max(get_ball_hist[0]), f'Mean = {mean:.2f}', ha='right', va='bottom', color='red')
    return get_ball_hist

def opp_get_ball_analysis(opp_get_ball):
    get_ball_hist = plt.hist(opp_get_ball, bins = 50, edgecolor='black', color='orange')
    plt.title('Time Left on Clock vs. Double Dip Tendency')
    plt.xlabel('Time Left on Clock (Opponent Final Drive)')
    plt.ylabel('Frequency of Double Dip')
    mean = stat.mean(opp_get_ball)
    plt.axvline(mean, color='red', linestyle='dashed', linewidth=2, label=f'Mean = {mean}')
    plt.text(mean, max(get_ball_hist[0]), f'Mean = {mean:.2f}', ha='right', va='bottom', color='red')
    return get_ball_hist

def time_last_score(double_dip, time1, time2):
    time_list = []
    score_percent_list = []
    points_means_list = []
    epa_mean_list = []
    total_values_list = []

    while time1 < 230 or time2 < 240:
        time_list.append(f"{time1}-{time2}")

        no_score_count = 0
        score_count = 0

        scoring_list = []  # Clear the list at the start of each time interval

        for index in range(len(double_dip)):
            first_team = double_dip[index][0]
            second_team = double_dip[index][1]
            first_team_last_q2_secs = first_team['last_q2_secs']
            second_team_last_q2_secs = second_team['last_q2_secs']

            # Initialize scoring_event with a default value
            scoring_event = None

            # Check if either team's last_q2_secs is within the time range
            if (time1 <= first_team_last_q2_secs <= time2):
                if first_team_last_q2_secs < second_team_last_q2_secs:
                    scoring_event = first_team["last_drive_end_event_q2"]
                    scoring_time = first_team_last_q2_secs
                elif second_team_last_q2_secs > first_team_last_q2_secs:
                    scoring_event = second_team["last_drive_end_event_q2"]
                    scoring_time = second_team_last_q2_secs

            if scoring_event is not None:  # Check if scoring_event is assigned
                if scoring_event == 0:
                    no_score_count += 1
                elif scoring_event == 3 or scoring_event == 6:
                    score_count += 1

                score_entry = (scoring_event,
                               scoring_time,
                               first_team["points"],
                               first_team["epa_sum"])

                # Check if the entry is not already in the list before appending
                if score_entry not in scoring_list:
                    scoring_list.append(score_entry)

        if no_score_count + score_count > 0:
            total_values = no_score_count + score_count
            score_percent = (score_count / (no_score_count + score_count))
        else:
            score_percent = 0.0  # Handle division by zero
        
        total_values_list.append(total_values)
        score_percent_list.append(score_percent)

        # Calculate points_means_list and epa_mean_list
        points_list = [value[2] for value in scoring_list]
        epa_list = [epa[3] for epa in scoring_list]
        points_mean = stat.mean(points_list)
        epa_mean = stat.mean(epa_list)
        points_means_list.append(points_mean)
        epa_mean_list.append(epa_mean)

        time1 = time1 + 10
        time2 = time2 + 10

    return score_percent_list, time_list, points_means_list, epa_mean_list, total_values_list  

def print_time_bins_results(double_dip):
    time1 = 10

    while time1 < 230:
        time2 = time1 + 10  # Set the end of the time interval

        score_percent_list, time_list, points_means_list, epa_mean_list, total_values_list = time_last_score(double_dip, time1, time2)

        # Print one time interval and its results at a time
        print("Time Interval:", time_list[0])
        print("Score Percentage:", score_percent_list[0])
        print("Points Mean:", points_means_list[0])
        print("EPA Mean:", epa_mean_list[0])
        print("Total Values:", total_values_list[0])
        print("\n")

        time1 = time2

def last_score_time_analysis(last_score_drive, last_drive_time):
    score_time = plt.bar(last_drive_time, last_score_drive, edgecolor='black')
    plt.title('Percent Scoring vs Time Remaining in Half')
    plt.xlabel('Time Remaining in Half')
    plt.xticks(range(len(last_drive_time)), last_drive_time, rotation='vertical')
    plt.ylabel('Percent Score')
    return score_time    

def points_time_analysis(last_drive_time, points_means_list):
    points_time = plt.bar(last_drive_time, points_means_list, edgecolor='black')
    plt.title('Average Points vs Time Remaining in Half')
    plt.xlabel('Time Remaining in Half')
    plt.xticks(range(len(last_drive_time)), last_drive_time, rotation='vertical')
    plt.ylabel('Average Points')
    return points_time    

def epa_analysis(last_drive_time, points_means_list, epa_means_list):
    difference_list = []
    for i, j in zip(points_means_list, epa_means_list):
        difference = i - j
        difference_list.append(difference)
    difference_graph = plt.bar(last_drive_time, difference_list, edgecolor='black')
    plt.title('Time Remaining in Half vs EPA and Actual Point Difference')
    plt.xlabel('Time Remaining in Half')
    plt.xticks(range(len(last_drive_time)), last_drive_time, rotation='vertical')
    plt.ylabel('Expected vs Actual Points Difference')
    return difference_graph

def field_position(double_dip):
    field_position_list = []
    field_po_list_label = []
    no_score = []
    score = []
    field_goal = []
    touchdown = []
    score_percent_list = []
    combined_list = []
    points_list = []
    epa_list = []
    points_means_list = []
    epa_mean_list = []
    pos1 = 99
    pos2 = 95
    while pos2 > 0:
        pos1 = pos1 - 5
        pos2 = pos2 - 5
        field_po_list_label.append(f"{pos1}-{pos2}")

        score_count = 0
        no_score_count = 0
        
        for index in range(len(double_dip)):
            first_team = double_dip[index][0]
            second_team = double_dip[index][1]
            first_team_last_q2_secs = first_team['last_q2_secs']
            second_team_last_q2_secs = second_team['last_q2_secs']
            
            if first_team_last_q2_secs < second_team_last_q2_secs:
                field_position_list.append((first_team["last_drive_end_event_q2"],
                                     first_team["last_q2_secs"],
                                     first_team["points"],
                                     first_team["last_drive_q2_start_field_position"]))
            if second_team_last_q2_secs > first_team_last_q2_secs:
                field_position_list.append((second_team["last_drive_end_event_q2"],
                                     second_team["last_q2_secs"],
                                     second_team["points"],
                                     second_team["last_drive_q2_start_field_position"]))
                
        for result in field_position_list:
            if result[0] == 0 and pos1 >= result[3] >= pos2:
                no_score.append(result)
                no_score_count += 1
            elif result[0] == 3 and pos1 >= result[3] >= pos2:
                field_goal.append(result)
                score.append(result)
                score_count +=1
            elif result[0] == 6 and pos1 >= result[3] >= pos2:
                touchdown.append(result)
                score.append(result)
                score_count += 1
        score_percent = score_count/(no_score_count + score_count)
        score_percent_list.append(score_percent)
        combined_list = score + no_score
        points_list = [value[2] for value in combined_list]
        epa_list = [epa[3] for epa in combined_list]
        points_mean = stat.mean(points_list)
        points_means_list.append(points_mean)   
        epa_mean = stat.mean(epa_list)
        epa_mean_list.append(epa_mean)
    return score_percent_list, field_po_list_label, points_means_list, epa_mean_list, combined_list

def field_position_analysis(x, y):
    field_pos_score = plt.bar(y, x, edgecolor='black')
    plt.title('Percent Scoring vs. Field Position')
    plt.xlabel('Field Position To Go')
    plt.xticks(range(len(y)), y, rotation='vertical')
    plt.ylabel('Percent Score')
    return field_pos_score

def field_position_epa(y, z, a):    
    difference_list = []
    for i, j in zip(z, a):
        difference = i - j
        difference_list.append(difference)
    field_epa_graph = plt.bar(y, difference_list, edgecolor='black')
    plt.title('Field Position vs EPA and Actual Point Difference')
    plt.xlabel('Field Position')
    plt.xticks(range(len(y)), y, rotation='vertical')
    plt.ylabel('Expected vs Actual Points Difference')
    return field_epa_graph

if __name__ == "__main__":
    drives = load_drives()
    total_points(drives)
    new_field_pos(drives)
    total_epa(drives)
    convert_times(drives)
    drives_dict = coup(drives)
    double_dip = dubdip(drives_dict)
    drive_time, opp_drive_time, get_ball, opp_get_ball = length_drive(double_dip)
    #second_last_time_hist, second_last_time_sumtab = drive_time_analysis(drive_time)
    #opp_final_drive_time_analysis, opp_final_drive_time_sumtab = opp_drive_time_analysis(opp_drive_time)
    #get_ball_analysis(get_ball)
    opp_get_ball_analysis(opp_get_ball)
    last_drive_score, last_drive_time, points_means_list, epa_means_list, total_values_list = time_last_score(double_dip, time1=10, time2=20)
    #print_time_bins_results(double_dip)
    #last_score_time_a = last_score_time_analysis(last_drive_score, last_drive_time)
    #points_time_a = points_time_analysis(last_drive_time, points_means_list)
    #point_dif_a = epa_analysis(last_drive_time, points_means_list, epa_means_list)
    #point_dif_a
    #x, y, z, a, b = field_position(double_dip)
    #print(scoring_list)
    #field_pos_a = field_position_analysis(x,y)
    #field_position_epa(y, z, a)
