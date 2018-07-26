import sqlite3
import yaml
import re
'''
desc table: PRAGMA table_info(projects_usage)
add column: alter table projects_usage add column active varchar(1) default "Y"
'''

def loadfile2db(file='projects_usage_rate.records', db="projects_usage.db"):
    with open(file, 'rb') as f:
        data = yaml.load(f.read())

    cx = sqlite3.connect(db)
    cu = cx.cursor()
    cu.execute("drop table projects_usage")
    cu.execute("""create table IF NOT EXISTS projects_usage \
                (name varchar(32), host varchar(16), active varchar(1), \
                instance int(4), connection int(4), date varchar(20), \
                primary key (name,date))""")
    for d in data:
        host = d['host']
        timestamp = d['date']
        for p in d['projects']:
            k = p.keys()[0]
            v = p.values()[0]
            cu.execute("insert into projects_usage (name, host, active, instance, connection, date) values \
                    ('%s', '%s', '%s', %d, %d, '%s')"%(k, host, v['enable'] and 'Y' or 'N', \
                                                 v['instance'], v['connection'], timestamp))
    cx.commit()
    cu.close()
    cx.close()


def loadmissingdata2db(file='projects_usage_rate.records', db="projects_usage.db"):
    with open(file, 'rb') as f:
        data = yaml.load(f.read())
    cx = sqlite3.connect(db)
    cu = cx.cursor()
    cu.execute("select max(date) from projects_usage")
    date_max = cu.fetchall()[0][0]
    for d in data:
        host = d['host']
        timestamp = d['date']
        if timestamp > date_max:
            for p in d['projects']:
                k = p.keys()[0]
                v = p.values()[0]
                cu.execute("insert into projects_usage (name, host, active, instance, connection, date) values \
                        ('%s', '%s', '%s', %d, %d, '%s')"%(k, host, v['enable'] and 'Y' or 'N', \
                                                     v['instance'], v['connection'], timestamp))
    cx.commit()
    cu.close()
    cx.close()

def alter_table(db='projects_usage.db'):
    cx = sqlite3.connect(db)
    cu = cx.cursor()
    cu.execute("alter table projects_usage add column floatingips varchar(96) default ''")
    cx.commit()
    cu.close()
    cx.close()