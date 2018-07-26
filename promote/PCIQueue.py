#-*- encoding:utf-8 -*-
'''
Created on 2018年4月24日

@author: sshentu
'''
from optparse import OptionParser
import sys
import MySQLdb
import logging
logging.basicConfig(level = logging.INFO,format = '[%(asctime)s - %(name)s - %(levelname)s] %(message)s')
logger = logging.getLogger(__name__)
table_pciqueue="il_ci_dashboard_ilpciqueue"

class QueueParameterException (Exception):
    pass
class MysqlOperator:
    def __init__(self, SERVER=None, USER=None, PASSWORD=None, DATABASE=None, PORT=3306):
        self.__SERVER = SERVER
        self.__USER = USER
        self.__PASSWORD = PASSWORD
        self.__DATABASE = DATABASE
        self.__PORT = PORT
        
    def connectDB(self):
        try:
            self.__conn = MySQLdb.connect(host=self.__SERVER, user=self.__USER, passwd=self.__PASSWORD, db=self.__DATABASE, port=self.__PORT)
        except Exception, ex:
            print str(ex) + " \ connect database failed: "
        self.__cur=self.__conn.cursor()
        return self.__cur
        
    def execute(self, sql,args=None):
        try:
            self.__cur.execute(sql,args)
        except Exception, ex:
            if str(ex)=="(1065, 'Query was empty')":
                pass
            else:
                print str(ex) + '\naccess database wrong'
            
    def fetchall(self):      
        return self.__cur.fetchall()
    
    def commit(self):
        self.__conn.commit()
    
    def fetchone(self):
        return self.__cur.fetchone()

    def closeDB(self):
        self.__cur.close()
        self.__conn.close()
        
    def rollback(self):
        self.__conn.rollback()
        
    def setTimezone(self):
        try:
            self.__cur.execute('SET time_zone = "+8:00";')
            self.__conn.commit()
        except Exception as e:
            logger.error("%s"%e,exc_info=True)
            self.__conn.rollback()
            
class Actions(object):
    def __init__(self,db,opt):
        self.db=db
        self.subsystem=opt.Subsystem
        self.PromoteVersion=opt.PromoteVersion
        self.Dependency=opt.Dependency
        self.TestCase=opt.TestCase
        
    def push(self):
        query='''
        SELECT * FROM `%s` WHERE `Subsystem` LIKE '%%%s%%' AND `PromoteVersion` LIKE '%%%s%%' ORDER BY `PushTime` DESC LIMIT 0, 1000
        '''%(table_pciqueue,self.subsystem,self.PromoteVersion)
        self.db.execute(query)
        query_result=self.db.fetchone()
        if query_result:
#             logger.info(query_result)
            query_result_id=query_result[0]
            update_sql='''
            UPDATE %s SET PushTime=CURRENT_TIMESTAMP, PromoteVersion = "%s", Dependency ="%s",IsInQueue="1" WHERE id="%s"
            '''%(table_pciqueue,self.PromoteVersion,self.Dependency,query_result_id)
            try:
                self.db.execute(update_sql)
                self.db.commit()
            except Exception as e:
                logger.error("%s"%e,exc_info=True)
                self.db.rollback()
        else:
            insert_sql='''
            INSERT INTO `%s`
            (Subsystem,Priority,PromoteVersion,Dependency,Header,TestCase,IsInQueue,PushTime,PopTime,Comments,CCIFtUrl,BuildName,PushedManually,NotReadyCase,Sack) 
            VALUES 
            ('%s', 3, '%s', '%s', '', '', 1, CURRENT_TIMESTAMP, NULL, NULL, '', NULL, 0, '', NULL);
            '''%(table_pciqueue,self.subsystem,self.PromoteVersion,self.Dependency)
            try:
                self.db.execute(insert_sql)
                self.db.commit()
            except Exception as e:
                logger.error("%s"%e,exc_info=True)
                self.db.rollback()
    def check(self):
        query='''
        SELECT * FROM `%s` WHERE `IsInQueue` = '1' ORDER BY `PushTime` DESC LIMIT 0, 1000
        '''%(table_pciqueue)
        self.db.execute(query)
        query_result=self.db.fetchall()
        subsystem_inqueue=[]
        for one in query_result:
            ss_name=one[1]
            ss_version=one[3]
            item="%s@%s"%(ss_name,ss_version)
            subsystem_inqueue.append(item)
        if len(subsystem_inqueue)==0:
            raise Exception("there is no subsystem in promote queue")
        
        query='''
        SELECT * FROM `%s` WHERE `Subsystem` LIKE '%%%s%%' AND `PromoteVersion` LIKE '%%%s%%' ORDER BY `PushTime` DESC LIMIT 0, 1000
        '''%(table_pciqueue,self.subsystem,self.PromoteVersion)
        self.db.execute(query)
        query_result=self.db.fetchone()
        if query_result is None:
            raise Exception("subsystem %s is not in promote queue"%self.subsystem)
        subsystem_dependency=[]
        subsystem_dependency.append("%s@%s"%(query_result[1],query_result[3]))
        if query_result[4].strip():
            subsystem_dependency+=query_result[4].strip().split(':')
        dependency_notInQueue=set(subsystem_dependency)-(set(subsystem_dependency) & set(subsystem_inqueue))
        if len(dependency_notInQueue) :#dependency inqueue
            raise Exception("%s's dependency %s is not queue"%(self.subsystem," ".join(dependency_notInQueue)))
        else:
            logger.info("%s's dependency %s all is in queue"%(self.subsystem," ".join(subsystem_dependency)))
            # pop need done by SCM
#             for item in subsystem_dependency:
#                 logger.info("pop %s"%item)
#                 ss,promoteVersion=item.split('@')
#                 update_sql='''
#                 UPDATE `%s` SET `IsInQueue`='0' WHERE (`Subsystem`='%s' AND `PromoteVersion`='%s')
#                 '''%(table_pciqueue,ss,promoteVersion)
#                 try:
#                     self.db.execute(update_sql)
#                     self.db.commit()
#                 except Exception as e:
#                     logger.error("%s"%e,exc_info=True)
#                     self.db.rollback()

class options(object):
    def __init__(self):
        pass
    
def validate_parameter(args):
    if len(args) < 3:
        raise QueueParameterException("Not enough parameter for subcommand: " + args[0])

haveRevision = lambda s: True if s.find("@")!=-1 else False
def validate_opts(opts):
    if opts.testCases and not haveRevision(opts.testCases):
        raise QueueParameterException("testCases must add peg revision number ")
    if opts.depends and not haveRevision(opts.depends):
        raise QueueParameterException("dependencies must add revision")
    
if __name__ == '__main__':
    
    version='$Id: PCIQueue.py  1.0$'
    usage_info = 'PCIQueue.py <sub_command> [options]\n\n'
    usage_info += 'push: \n    put a subsystem to PCI Queue\n'
    usage_info += '    EXAMPLE: push <subsystem> <version> [-IHeader1[:Header2]] [-TTestCase1[:TestCase2]] [-DDependecy1[:Dependecy2]] [-UCCIFTURL] [-M True/False]\n\n'
    usage_info += 'check: \n    check subsystems from PCI Queue to PCI\n\n'

    parser = OptionParser(usage_info, version=version)
    parser.add_option("-D", "--dependency", dest="depends", help="the dependencies of subsystem")
    parser.add_option("-T", "--testcase", dest="testCases", help="the test case of subsystem")
    parser.add_option("--db", dest="database", help="set database if nessary, can be added after any command")
    
    opts, args = parser.parse_args()
    dbImpl=None
    try:
        validate_parameter(args)
        validate_opts(opts)
        DB_NAME=opts.database
        dbImpl = MysqlOperator(SERVER='hzdatav01.china.nsn-net.net', USER='root', PASSWORD='ILMAN@db', DATABASE=DB_NAME, PORT=3306)
        dbCursor=dbImpl.connectDB()
        dbImpl.setTimezone()
        
        actions=args[0]
        option=options()
        setattr(option, 'Subsystem', args[1])
        setattr(option, 'PromoteVersion', args[2])
        setattr(option, 'Dependency', opts.depends if opts.depends else "")
        setattr(option, 'TestCase', opts.testCases if opts.testCases else "")
        queueAction=Actions(dbImpl,option)
        if actions.lower()=="push":
            queueAction.push()
        elif actions.lower()=="check":
            queueAction.check()
        else:
            raise QueueParameterException("action %s not availiable"%(actions))
    except QueueParameterException,pe:
        logger.error("ERROR: ***%s" %(pe),exc_info=True)
        logger.info("Type 'PCIQueue.py -h or PCIQueue.py --help' for usage.")
        sys.exit(1)
    except Exception,e :
        logger.error("ERROR: ***%s" %(e),exc_info=True)
        sys.exit(1)
    finally:
        if dbImpl is not None:
            dbImpl.closeDB()
