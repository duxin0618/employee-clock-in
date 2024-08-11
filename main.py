# 读取csv文件
import csv
from datetime import datetime, timedelta, time
import os
import sys

def read_csv(file):
    current_month_records = []
    with open(file, newline='', encoding='gbk') as csvfile:
        csvreader = csv.reader(csvfile)
        for id, row in enumerate(csvreader):
            if id == 0: # 第一行是表头
                continue
            current_month_records.append(row)

    # employee_names = set()
    # for id, record in enumerate(current_month_records):
    #     if len(record[1]) == 1:
    #         continue
    #     employee_names.add(record[1])

    return current_month_records

# 写入员工姓名
def write_csv(file, data, not_in_employee=None):
    with open(file, 'w', newline='', encoding='gbk') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["姓名", "日期", "上班时间", "下班时间", "上班情况", "迟到时长", "下班情况", "早退/加班时长", "异常情况"])
        for row in data:
            if len(row) == 1:
                csvwriter.writerow([row])
            csvwriter.writerow(row)
        if not_in_employee:
            for row in not_in_employee:
                csvwriter.writerow([row])
        

#  读取所有的员工姓名
def read_all_employee(file):
    all_employee = set()
    with open(file, newline='', encoding='gbk') as csvfile:
        csvreader = csv.reader(csvfile)
        for id, row in enumerate(csvreader):
            all_employee.add(row[0])

    return all_employee

def process_employee_record(current_month_records, employee_names):
    not_in_employee = []
    employee_records = {}
    for id, record in enumerate(current_month_records):
        if record[1] not in employee_names:
            not_in_employee.append(["不在员工名单中", record])
            continue
        
        # 2024/3/15 9:04
        # 获取日期和时间
        time_obj = datetime.strptime(record[3], '%Y-%m-%d %H:%M:%S')  
        date = time_obj.strftime('%Y-%m-%d')  # 提取日期  
        time_of_day = time_obj.time()  # 提取时间

        if record[1] in employee_records:
            if date in employee_records[record[1]]:
                employee_records[record[1]][date].append(time_of_day)
            else:
                employee_records[record[1]][date] = [time_of_day]
        else:
            employee_records[record[1]] = {date: [time_of_day]}

    # print("not_in_employee: ", not_in_employee)
    # print("employee_records: ", employee_records[employee_names.pop()])
    return employee_records, not_in_employee
# 判断员工迟到和早退和加班的时间
def judge_late_early_overtime(employee_records, not_in_employee, save_file):
    aux = []
    for employee, records in employee_records.items():
        for date, times in records.items():
            if len(times) == 1:
                first = str(date) + ' ' + str(times[0])
                up, down, error = check_time([first])
                # print([f"员工{employee}", f"日期: {date}", f"{up}", "缺少下班打卡"])
                if len(up) > 0:
                    aux.append([f"{employee}", f"日期: {date}", f"上班时间: {str(times[0])}", "", f"{up[0]}", f"{up[1]}", "缺卡", "", f"{error[0]}"])
                else:
                    aux.append([f"{employee}", f"日期: {date}", "", f"下班时间: {str(times[0])}", "缺卡", "", f"{down[0]}", f"{down[1]}", f"{error[0]}"])
            else:
                first = str(date) + ' ' + str(times[0])
                second = str(date) + ' ' + str(times[-1])
                up, down, error = check_time([first, second])
                aux.append([f"{employee}", f"日期: {date}", f"上班时间: {str(times[0])}", f"下班时间: {str(times[-1])}", f"{up[0]}", f"{up[1]}", f"{down[0]}", f"{down[1]}", f"{error[0]}"])
                # print([f"员工{employee}", f"日期: {date}", f"{up}", f"{down}"])
    
    write_csv(save_file, aux, not_in_employee=not_in_employee)

# 判断时间是否迟到早退
def check_time(time_strs):  
    # 解析时间字符串 
    result_up = []
    result_down = []
    result_error = ['']*len(time_strs)
    # 按时间顺序排序，确保第一个是上班打卡时间，第二个是下班打卡时间
    time_strs = sorted(time_strs)
    date = ''
    uo_or_down = 'up'
    for id, time_str in enumerate(time_strs):
        time_obj = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')  
        date = time_obj.strftime('%Y-%m-%d')  # 提取日期  
        time_of_day = time_obj.time()  # 提取时间  
    
        # 定义上下午的时间点  
        morning_check = datetime.combine(time_obj.date(), time(7, 30))  
        afternoon_check = datetime.combine(time_obj.date(), time(17, 0))
        overtime_start = datetime.combine(time_obj.date(), time(17, 30)) 

        # 定义一次打卡的判断上下午的时间阈值
        up_certion = datetime.combine(time_obj.date(), time(10, 0))
        down_certion = datetime.combine(time_obj.date(), time(16, 00))

        if id == 0:
            up_or_down = 'up'
        else:
            up_or_down = 'down'

        # 当仅仅打卡一次时
        if len(time_strs) == 1:
            if time_obj <= up_certion:
                up_or_down = 'up'
            elif time_obj >= down_certion:
                up_or_down = 'down'
            else:
                result_error[id] = '打卡异常，无法判断考勤时间'

  
        # 判断是上午还是下午  
        if up_or_down == 'up':  
            # 上午/下午  
            if time_obj > morning_check:  
                # 迟到  
                late_minutes = (time_obj - morning_check).total_seconds() // 60  
                if late_minutes == 0:
                    result_up.append("正常")
                    result_up.append('')
                else:
                    result_up.append("迟到")
                    result_up.append(f"迟到 {late_minutes} 分钟")
                   
            else:  
                # 正常  
                result_up.append("正常")
                result_up.append('')
        else:  
            # 下午  
            if time_obj < afternoon_check:  
                # 早退  
                early_minutes = (afternoon_check - time_obj).total_seconds() // 60  
                if early_minutes == 0:
                    result_down.append("早退")
                    result_down.append('早退 1 分钟')
                else:
                    result_down.append("早退")
                    result_down.append(f"早退 {early_minutes} 分钟")
            else: 
                # 晚上（假设17:30之后为加班时间）  
                if time_obj >= overtime_start:  
                    # 加班  
                    overtime_minutes = (time_obj - overtime_start).total_seconds() // 60  + 30
                    result_down.append("加班")
                    result_down.append(f"加班 {overtime_minutes} 分钟")
                else:  
                    # 正常（虽然这种情况在这个逻辑下不太可能发生，但为了完整性还是保留）  
                    result_down.append("正常")
                    result_down.append('')
    return result_up, result_down, result_error



if __name__ == '__main__':    
    # 获取当前文件的完整路径  
    current_directory = os.path.dirname(os.path.realpath(sys.argv[0]))
    # print(current_directory)
    # 获取所有员工姓名
    employee_names = read_all_employee(current_directory+'/employee/employee.csv')
    
    # 获取当前文件夹下所有文件的列表  
    files = os.listdir(current_directory+"/data")  # 列出目录中的文件和文件夹  
    
    # 遍历文件列表，查找.csv文件  
    for file in files:  
        if file.endswith('.csv') and file != 'employee.csv' and 'result' not in file: 
            current_month_records = read_csv(current_directory+"/data/"+file)
            employee_records, not_in_employee = process_employee_record(current_month_records, employee_names)
            judge_late_early_overtime(employee_records, not_in_employee, current_directory+"/result/"+file.split('.')[0]+'_result.csv')



