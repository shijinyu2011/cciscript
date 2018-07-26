import yaml
import datetime
import time
import sqlite3
import re
import os
import sys

class Report(object):
    def __init__(self, source, start_date, end_date):
        self.source = source
        self.start_date = start_date
        self.end_date = end_date
        self.week = int(datetime.datetime.strptime(self.start_date, '%Y-%m-%d').strftime("%W"))+1

    def load_yaml_records(self):
        with open(self.source, 'rb') as f:
            data = f.read()
        return yaml.load(data)
    
    def load_db_records(self):
        cx = sqlite3.connect(self.source)
        cu = cx.cursor()
        cu.execute("select distinct host from projects_usage")
        hosts = cu.fetchall()
        cu.execute("select distinct from projects_usage where host='%s'"%host)
        projects = cu.fetchall()
        cx.commit()
        cu.close()
        cx.close()

    def execute_sql(self, sql):
        cx = sqlite3.connect(self.source)
        cu = cx.cursor()
        cu.execute(sql)
        result = cu.fetchall()
        cx.commit()
        cu.close()
        cx.close()
        return result

    def _aggregate_data(self, round_hour='00-24'):
        starth, endh = round_hour.split('-')
        sql = 'select name, host, substr(date, 1, 10), group_concat(instance), group_concat(connection) \
            from projects_usage where active="Y" and date>"%s" and date<"%s" and \
            substr(date, 12, 2)>"%s" and substr(date,12, 2)<"%s" group by name, host, substr(date, 1, 10) \
            order by date'%(self.start_date, self.end_date, starth, endh)
        sql_data = self.execute_sql(sql)
        results = {}
        for d in sql_data:
            date = d[2]
            host = d[1]
            project = results.setdefault(host, {}).setdefault(d[0], {})
            project.setdefault(date, {}).setdefault('instance', [int(i) for i in d[3].split(',')])
            project.setdefault(date, {}).setdefault('connection', [int(i) for i in d[4].split(',')])
        return results

    def daily_chart(self):
        def _get_project_details(host, project):
            sql = 'select date, instance, connection from projects_usage where active="Y" and host="%s" \
                  and name="%s" and date>"%s" and date<"%s" order by date' % (host, project, self.start_date, self.end_date)
            details = self.execute_sql(sql)
            d2t = lambda x: int(time.mktime(time.strptime(x, '%Y-%m-%d %H:%M:%S'))*1000)
            instance_details = [[d2t(d[0]), d[1]] for d in details]
            connection_details = [[d2t(d[0]), d[2]] for d in details]
            return instance_details, connection_details

        from templates import daily_template
        results = self._aggregate_data()
        for h in results:
            projects = results[h]
            for p in projects:
                date = projects[p]
                for d in date:
                    instances = filter(lambda x: x>0, date[d]['instance']).__len__()
                    connections = filter(lambda x: x>0, date[d]['connection']).__len__()
                    total = date[d]['instance'].__len__()
                    instance_rate = "%0.2f" % (float(instances)/total*100)
                    connection_rate = "%0.2f" % (float(connections)/total*100)
                    date[d]['instance'] = instance_rate
                    date[d]['connection'] = connection_rate
                    i, c = _get_project_details(h, p)
                self._dump_to_html(h, p, date, i, c, daily_template)

    def _dump_to_html(self, host, project, data, instance_details, connection_details, template):
        x_axis = [x.encode('ascii') for x in data.keys()]
        x_axis.sort()
        instance = [float(data.get(x)['instance']) for x in x_axis] 
        connection = [float(data.get(x)['connection']) for x in x_axis]
        y_axis = [{'name': 'instance', 'data':instance}, {'name':'connection', 'data': connection}]
        content = template %{'host': host, 'project': project, \
                             'xaxis': x_axis, 'yaxis': y_axis, \
                             'start_date':x_axis[0], 'end_date':x_axis[-1], \
                             'instance_details':instance_details, 'connection_details':connection_details}
        if not os.path.exists('./projects_details'):
            os.makedirs('./projects_details')
        with open("./projects_details/%s-%s-report.html"%(project, host), 'wb') as f:
            f.write(content)

    def projects_usage_daily_report(self):
        x_dates_sql = 'select distinct substr(date, 1, 10) from projects_usage where active="Y" and date>"%s" and date<"%s"'%(self.start_date,self.end_date )
        x_dates = self.execute_sql(x_dates_sql)
        x_dates = [x[0] for x in x_dates]
        x_dates.sort()

        sql = 'select name, host, group_concat(instance), group_concat(connection) from projects_usage \
            where active="Y" and date>"%s" and date<"%s" group by name, host order by date'%(self.start_date, self.end_date)
        results = self.execute_sql(sql)
        project_summary = []
        for r in results:
            name = r[0]
            host = r[1]
            if re.match('(?i)admin|services|CCI-Monitor-.*', name):
                continue
            valid_instance = filter(lambda x: int(x)>0, r[2].split(',')).__len__() or 1
            valid_connection = filter(lambda x: int(x)>0, r[3].split(',')).__len__()
            usage_rate = "%0.2f"%(float(valid_connection)/valid_instance*100)
            project_summary.append([name, host, usage_rate])
        project_summary.sort(lambda x, y: cmp(float(y[2]), float(x[2])))

        details = self._aggregate_data()
        html = '<html><body><h4>Week%s(%s - %s)<h4><table width="50%%" style="border-collapse: collapse" border="1"><tr><th>Project</th><th>Host</th><th>' \
                + '</th><th>'.join([x[5:] for x in x_dates]) + '</th><th>Total</th></tr>\n'
        html = html % (self.week, x_dates[0], x_dates[-1])
        for i in project_summary:
            html += '<tr><td>%s</td><td>%s</td>' % (i[0], i[1])
            projects = details.get(i[1])
            if projects is None:
                continue
            date = projects.get(i[0])
            
            print i[1], i[0], date, details.get(i[1]).keys()
            for x in x_dates:
                if date and date.has_key(x):
                    valid_instance = filter(lambda m: m>0, date[x]['instance']).__len__() or 1
                    valid_connection = filter(lambda m: m>0, date[x]['connection']).__len__()
                    usage_rate = "%0.2f" % (float(valid_connection)/valid_instance*100,)
                else:
                    usage_rate = ''
                html += '<td>%s</td>'%usage_rate
            html += '<td>%s</td></tr>\n' % i[2]
        html += '</table></html>'
        file_name = "project_usage_report_Week%s.html"%self.week
        with open(file_name, 'wb') as f:
            f.write(html)

    def projects_usage_hourly_report(self):
        record_hosts = ('10.70.56.64',)
        record_projects = ('DA1-Launcher-R', 'DA1-Bugatti-R','DA1-Walle-R','DA1-Matrix-R','DA1-Sorcery-R','DA1-Turbo-R')
        x_dates_sql = 'select distinct substr(date, 1, 10) from projects_usage \
                    where active="Y" and date>"%s" and date<"%s"'%(self.start_date, self.end_date)
        x_dates = self.execute_sql(x_dates_sql)
        x_dates = [x[0] for x in x_dates]
        x_dates.sort()
        
        sql = 'select name, host, group_concat(instance), group_concat(connection) from projects_usage \
            where active="Y" and date>"%s" and date<"%s" group by name, host order by date'%(self.start_date, self.end_date)
        results = self.execute_sql(sql)
        project_summary = []
        for r in results:
            name = r[0]
            host = r[1]
            if not (host in record_hosts and name in record_projects):
                continue
            valid_instance = filter(lambda x: int(x)>0, r[2].split(',')).__len__() or 1
            valid_connection = filter(lambda x: int(x)>0, r[3].split(',')).__len__()
            usage_rate = "%0.2f"%(float(valid_connection)/valid_instance*100)
            project_summary.append([name, host, usage_rate])
        project_summary.sort(lambda x, y: cmp(float(y[2]), float(x[2])))

        details0914 = self._aggregate_data('09-14')
        details1418 = self._aggregate_data('14-18')
        details1821 = self._aggregate_data('18-21')
        str2weekday = lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').strftime('%A')
        html = '<html><body><h4>Week%s(%s - %s)<h4><table width="50%%" style="border-collapse: collapse" border="1"><tr><th>Week%s</th><th></th><th></th><th>' \
                + '</th><th>'.join([str2weekday(x) for x in x_dates]) + '</th><th rowspan="2">Total</th></tr>\n'
        html+='<tr><th></th><th></th><th></th><th>' \
                + '</th><th>'.join([x for x in x_dates]) + '</th></tr>'
        html = html % (self.week, x_dates[0], x_dates[-1], self.week)

        for i in project_summary:        
            html += '<tr><td rowspan="3" align="center">%s</td><td rowspan="3" align="center">%s</td>' % (i[0], i[1])
            html+='<td align="center">Morning9:00-14:00</td>'
           
            date = details0914.get(i[1]).get(i[0])
            
            for x in x_dates:
                if date and date.has_key(x):
                    valid_instance = filter(lambda m: m>0, date[x]['instance']).__len__() or 1
                    valid_connection = filter(lambda m: m>0, date[x]['connection']).__len__()
                    usage_rate = "%0.2f" % (float(valid_connection)/valid_instance*100,)
                else:
                    usage_rate = ''
                html += '<td align="center">%s</td>'%usage_rate            
            html += '<td rowspan="3" align="center">%s</td></tr>\n' % i[2]
            
            date1 = details1418.get(i[1]).get(i[0])
            
            html+='<tr>'
            html+='<td align="center">Afternoon14:00-18:00</td>'
            for x in x_dates:
                if date1 and date1.has_key(x):
                    valid_instance = filter(lambda m: m>0, date1[x]['instance']).__len__() or 1
                    valid_connection = filter(lambda m: m>0, date1[x]['connection']).__len__()
                    usage_rate = "%0.2f" % (float(valid_connection)/valid_instance*100,)
                else:
                    usage_rate = ''
                html += '<td align="center">%s</td>'%usage_rate
            html+='</tr>'
            
            date2 = details1821.get(i[1]).get(i[0])
            
            html+='<tr>'
            html+='<td align="center">Evening 18:00-21:00</td>'
            for x in x_dates:
                if date2 and date2.has_key(x):
                    valid_instance = filter(lambda m: m>0, date2[x]['instance']).__len__() or 1
                    valid_connection = filter(lambda m: m>0, date2[x]['connection']).__len__() 
                    usage_rate = "%0.2f" % (float(valid_connection)/valid_instance*100,)
                else:
                    usage_rate = ''
                html += '<td align="center">%s</td>'%usage_rate
            html+='</tr>'                
        html += '</table></html>'
      
        file_name = "project_usage_report_hourly_Week%s.html"%self.week
        with open(file_name, 'wb') as f:
            f.write(html)
    
    def print_detailed_sample(self, projects=("DA1-Phoenix-B-1", "DA1-Phoenix-B-1")):
        sql = 'select name, host, substr(date, 1, 10), group_concat(instance), group_concat(connection) from projects_usage \
            where active="Y" and date>"%s" and date<"%s" and name in %s \
            group by name, host, substr(date, 1, 10) order by date'%(self.start_date, self.end_date, projects)
        results = self.execute_sql(sql)
        for r in results:
            print r[2], "\ninstance: ", r[3], "\nconnection: ", r[4]

def main():
    if sys.argv.__len__() < 3:
        print "Please input start date and end date of the report"
        return
    o = Report('projects_usage.db', sys.argv[1], sys.argv[2])
#     o.daily_chart()
    o.projects_usage_daily_report()
    o.projects_usage_hourly_report()
#     o.print_detailed_sample()

if __name__ == "__main__":
     main()
