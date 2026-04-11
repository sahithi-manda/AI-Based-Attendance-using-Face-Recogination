import pandas as pd
import datetime
import os
from . import db_handler



def get_at_risk_students():
    """
    Flags students whose attendance has dropped by >= 15% in the last 14 days 
    compared to the 14 days prior to that.
    """
    try:
        df_students = pd.read_csv(db_handler.STUDENTS_CSV)
        if len(df_students) == 0:
            return []
            
        df_att = pd.read_csv(db_handler.ATTENDANCE_CSV)
        if df_att.empty:
            return []
            
        df_att['Date_Obj'] = pd.to_datetime(df_att['Date'])
        
        now = datetime.datetime.now()
        date_14_days_ago = now - datetime.timedelta(days=14)
        date_28_days_ago = now - datetime.timedelta(days=28)
        
        period1 = df_att[(df_att['Date_Obj'] > date_14_days_ago) & (df_att['Date_Obj'] <= now)]
        period2 = df_att[(df_att['Date_Obj'] > date_28_days_ago) & (df_att['Date_Obj'] <= date_14_days_ago)]
        
        p1_active_days = period1['Date'].nunique()
        p2_active_days = period2['Date'].nunique()
        
        if p1_active_days == 0 or p2_active_days == 0:
            return []
            
        p1_counts = period1['Roll_No'].astype(str).value_counts()
        p2_counts = period2['Roll_No'].astype(str).value_counts()
        
        at_risk = []
        for index, s_row in df_students.iterrows():
            roll = str(s_row['Roll_No'])
            name = s_row['Name']
            
            c1_val = p1_counts.get(roll, 0)
            c2_val = p2_counts.get(roll, 0)
            
            rate1 = (c1_val / p1_active_days) * 100
            rate2 = (c2_val / p2_active_days) * 100
            
            drop = rate2 - rate1
            if drop >= 15.0:
                at_risk.append({
                    "Roll_No": roll,
                    "Name": name,
                    "Drop_Percentage": round(drop, 1),
                    "Recent_Rate": round(rate1, 1),
                    "Previous_Rate": round(rate2, 1)
                })
                
        at_risk.sort(key=lambda x: x['Drop_Percentage'], reverse=True)
        return at_risk
    except Exception as e:
        print(f"Error in at-risk calc: {e}")
        return []

def get_predictive_alerts(total_semester_days=90):
    """
    Calculates current rate and projects if the student will fall below 75% 
    by the end of the semester based on their recent trend (last 14 days).
    """
    try:
        df_students = pd.read_csv(db_handler.STUDENTS_CSV)
        if df_students.empty:
            return []
            
        df_att = pd.read_csv(db_handler.ATTENDANCE_CSV)
        if df_att.empty:
            return []
            
        active_class_days = df_att['Date'].nunique()
        if active_class_days == 0:
            return []
            
        att_counts = df_att['Roll_No'].astype(str).value_counts()
        df_att['Date_Obj'] = pd.to_datetime(df_att['Date'])
        now = datetime.datetime.now()
        recent_period = df_att[df_att['Date_Obj'] > (now - datetime.timedelta(days=14))]
        recent_active_days = recent_period['Date'].nunique()
        recent_counts = recent_period['Roll_No'].astype(str).value_counts()
        
        alerts = []
        for index, s_row in df_students.iterrows():
            roll = str(s_row['Roll_No'])
            name = s_row['Name']
            
            attended = att_counts.get(roll, 0)
            current_rate = attended / active_class_days
            
            if recent_active_days > 0:
                recent_attended = recent_counts.get(roll, 0)
                trend_rate = recent_attended / recent_active_days
            else:
                trend_rate = current_rate
                
            remaining_days = max(0, total_semester_days - active_class_days)
            projected_final_attended = attended + (trend_rate * remaining_days)
            projected_final_rate = (projected_final_attended / total_semester_days) * 100
            current_rate_pct = current_rate * 100
            
            if projected_final_rate < 75.0:
                alerts.append({
                    "Roll_No": roll,
                    "Name": name,
                    "Current_Rate": round(current_rate_pct, 1),
                    "Projected_Rate": round(projected_final_rate, 1)
                })
                
        alerts.sort(key=lambda x: x['Projected_Rate'])
        return alerts
    except Exception as e:
        print(f"Error in predictive alerts: {e}")
        return []

def get_monthly_attendance(year, month):
    try:
        df_students = pd.read_csv(db_handler.STUDENTS_CSV)
        if df_students.empty:
            return [], "", ""
            
        df_att = pd.read_csv(db_handler.ATTENDANCE_CSV)
        if df_att.empty:
            return [], "", ""
            
        import calendar
        start_date_str = f"{year}-{month:02d}-01"
        last_day = calendar.monthrange(int(year), int(month))[1]
        end_date_str = f"{year}-{month:02d}-{last_day}"
        
        df_att['Date_Obj'] = pd.to_datetime(df_att['Date'])
        month_period = df_att[(df_att['Date_Obj'] >= start_date_str) & (df_att['Date_Obj'] <= end_date_str)]
        
        active_days = month_period['Date'].nunique()
        if active_days == 0:
            return [], start_date_str, end_date_str
            
        att_counts = month_period['Roll_No'].astype(str).value_counts()
        
        results = []
        for index, row in df_students.iterrows():
            roll = str(row['Roll_No'])
            name = row['Name']
            present_days = att_counts.get(roll, 0)
            percentage = (present_days / active_days) * 100
            
            results.append({
                "Roll_No": roll,
                "Name": name,
                "Total_Classes": active_days,
                "Attended": present_days,
                "Percentage": round(percentage, 2)
            })
            
        results.sort(key=lambda x: x['Roll_No'])
        return results, start_date_str, end_date_str
    except Exception as e:
        print(f"Error in monthly fetch: {e}")
        return [], "", ""

def get_overall_attendance():
    try:
        df_students = pd.read_csv(db_handler.STUDENTS_CSV)
        if df_students.empty:
            return []
            
        df_att = pd.read_csv(db_handler.ATTENDANCE_CSV)
        if df_att.empty:
            return []
            
        active_days = df_att['Date'].nunique()
        if active_days == 0:
            return []
            
        att_counts = df_att['Roll_No'].astype(str).value_counts()
        
        results = []
        for index, row in df_students.iterrows():
            roll = str(row['Roll_No'])
            name = row['Name']
            present_days = att_counts.get(roll, 0)
            percentage = (present_days / active_days) * 100
            
            results.append({
                "Roll_No": roll,
                "Name": name,
                "Total_Classes": active_days,
                "Attended": present_days,
                "Percentage": round(percentage, 2)
            })
            
        results.sort(key=lambda x: x['Roll_No'])
        return results
    except Exception as e:
        print(f"Error in overall fetch: {e}")
        return []
