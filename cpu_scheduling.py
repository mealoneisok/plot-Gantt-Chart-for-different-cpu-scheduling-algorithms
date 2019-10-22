import copy
import math
import matplotlib.pyplot as plt

class CPUScheduler:
    def __init__(self, burst_time, priority = [], arrival_time = [], pid = []):
        '''
        Parameters
        ----------
        burst_time : compulsory, the burst time of processes
        priority : optional, used only in priority-based cpu scheduling algorithms.
        arrival_time : optional, the arrival time of processes in ASCENDING order (SORTED)
        pid : optional, the name of processes, used to differentiate the process
        '''
        self.schemes = ['fcfs', 'sjf', 'min_priority', 'max_priority', 'rr']
        self.bts = burst_time
        self.cnt_jobs = len(self.bts)
        if pid and len(pid) != self.cnt_jobs:
            raise ValueError('the length of pid does not equal the job count: {}.'.format(self.cnt_jobs))
        else:
            pid = pid or list(range(self.cnt_jobs))
        if arrival_time and len(arrival_time) != self.cnt_jobs:
            raise ValueError('the length of arrival_time does not equal the job count: {}.'.format(self.cnt_jobs))
        elif not arrival_time:
            arrival_time = arrival_time or [0] * self.cnt_jobs
        else:
            for i in range(self.cnt_jobs): #make sure arrival_time is in ascending order
                if i < self.cnt_jobs - 1 and arrival_time[i] > arrival_time[i + 1]:
                    raise ValueError('arrival_time must be in ascending order.')
        if priority and len(priority) != self.cnt_jobs:
            raise ValueError('the length of priority does not equal the job count: {}.'.format(self.cnt_jobs))
        else:
            priority = priority or [0] * self.cnt_jobs
        
        self.pid = pid
        self.ats = arrival_time
        self.prts = priority

        self.jobs = {}
        for pid, at, bt, pty in zip(self.pid, self.ats, self.bts, self.prts):
            self.jobs[pid] = {'pid' : pid, 'at' : at, 'bt' : bt, 'pty' : pty}
    
    #time_quantum: only meaningful when the scheme is rr
    def transform(self, scheme = 'fcfs', preemptive = False, time_quantum = 1):
        '''
        Parameters
        ----------
        scheme : cpu scheduling algorithm, possible: fcfs, sjf, min_priority, max_priority, rr
        preemptive : only used in sjf, priority-based algorithm
        time_quantum : only used in rr algorithm
        
        Outputs
        -------
        prog : process progress details, used in plotting Gantt chart
        summary : process summary, including wt (waiting time), tat (turnaround time) and rt (response time)
        '''
        scheme = scheme.lower()
        if scheme not in self.schemes:
            raise ValueError('unknown CPU scheduling algorithm: {}'.format(scheme))
        rjobs = copy.deepcopy(list(self.jobs.values()))
        ready_q = []
        time = 0 #time unit
        cnt_job_done = 0
        curr_job = None
        
        summary = {}
        for pid in self.pid:
            summary[pid] = {'wt' : {}, 'tat' : {}, 'rt' : {}}
        prog = []
        
        while cnt_job_done != self.cnt_jobs:
            if rjobs:
                if curr_job is None and not ready_q and rjobs[0]['at'] > time: #cpu idle, move to next arrival time
                    time = rjobs[0]['at']
                while rjobs and rjobs[0]['at'] <= time: #add new processes to ready queue
                        ready_q.append(rjobs.pop(0))
    
            #fetch job from ready_q
            if scheme == 'fcfs':
                if curr_job is None:
                    curr_job = ready_q.pop(0) #first come first serve
            elif scheme in ['sjf', 'min_priority', 'max_priority']:
                if scheme == 'sjf':
                    criterion = 'bt'
                    pred = min
                elif scheme == 'min_priority':
                    criterion = 'pty'
                    pred = min
                else:
                    criterion = 'pty'
                    pred = max

                if curr_job is None:
                    curr_job = pred(ready_q, key = lambda j : j[criterion])  #the job with shortest burst time
                    ready_q.remove(curr_job)
                elif preemptive:
                    curr_job_ = pred(ready_q, key = lambda j : j[criterion])
                    if (curr_job_[criterion] == curr_job[criterion] and \
                        self.jobs[curr_job_['pid']]['at'] < self.jobs[curr_job['pid']]['at']) or \
                        (pred == min and curr_job_[criterion] < curr_job[criterion]) or \
                        (pred == max and curr_job_[criterion] > curr_job[criterion]):
                        ready_q.append(curr_job)
                        ready_q.remove(curr_job_)
                        curr_job = curr_job_
            elif scheme == 'rr':
                if curr_job is None:
                    curr_job = ready_q.pop(0)
                elif ready_q:
                    ready_q.append(curr_job)
                    curr_job_ = ready_q.pop(0)
                    curr_job = curr_job_

            et = time + curr_job['bt']  #end time
            btl = 0 #burst time left

            if scheme == 'rr':
                if et > time + time_quantum:
                    btl = curr_job['bt'] - time_quantum
                    et = time + time_quantum
            elif rjobs and et > rjobs[0]['at']:
                btl = et - rjobs[0]['at']
                et = rjobs[0]['at']

            curr_job['bt'] = btl

            #finish a progress
            if prog and prog[-1]['pid'] == curr_job['pid']:
                prog[-1]['et'] = et
            else:
                prog.append({'pid' : curr_job['pid'], 'st' : time, 'et' : et})

            if curr_job['bt'] == 0: #when a job is completed
                pid = curr_job['pid']
                summary[pid]['tat'] = et - self.jobs[pid]['at']
                summary[pid]['wt'] = summary[pid]['tat'] - self.jobs[pid]['bt']
                for prg in prog:
                    if pid == prg['pid']:
                        summary[pid]['rt'] = prg['et'] - self.jobs[pid]['at']
                        break
                cnt_job_done += 1
                curr_job = None

            time = et
        return prog, summary 

class ProcessGanttChart:    
    def transform(self, prog, gnt = None, title = 'cpu scheduling'):
        prc = sorted(set([p['pid'] for p in prog]))
        prc_cnts = len(prc)
        gnt = gnt or plt.gca()
        bar_w = 5
        bar_h = 5 * (prc_cnts + 2)
        gnt.set_ylim(0, bar_h) 
        gnt.set_xlim(0, prog[-1]['et']) 

        gnt.set_xlabel('time') 
        gnt.set_ylabel('process')
        gnt.set_title(title)
        
        gnt.set_xticks(range(0, prog[-1]['et'] + 1, math.ceil(prog[-1]['et'] / 10)))
        gnt.set_yticks([5 * prc_cnts - 5 * i + bar_w / 2 for i in range(prc_cnts)]) 
        gnt.set_yticklabels(prc)

        for i, prc in enumerate(prc):
            rng = []
            for prg in prog:
                if prg['pid'] == prc:
                    rng.append((prg['st'], prg['et'] - prg['st']))
            gnt.broken_barh(rng, (5 * prc_cnts - 5 * i, bar_w), facecolors = ('C{}'.format(i)))
        return gnt

if __name__ == '__main__':
    cpus = CPUScheduler(burst_time = [8, 1, 7, 7, 5, 4])
    prog, summ = cpus.transform(scheme = 'sjf', preemptive = False)
    pgc = ProcessGanttChart()
    gnt = pgc.transform(prog, title = 'sjf, nonpreemptive')
    plt.show(gnt)

    cpus2 = CPUScheduler(burst_time = [8, 1, 7, 7, 5, 4],
                        arrival_time = [0, 4, 8, 12, 17, 21],
                        priority = [5, 4, 2, 1, 6, 3],
                        pid = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6'])
    
    fig, gnt = plt.subplots(ncols = 2, nrows = 3, figsize = (15, 15))
    pgc = ProcessGanttChart()
    for i, (algo, pre, tq) in enumerate(zip(['fcfs', 'sjf', 'sjf', 'min_priority', 'min_priority', 'rr'], 
                                            [False, False, True, False, True, False], 
                                            [1, 1, 1, 1, 1, 5])):
        prog, summary = cpus2.transform(scheme = algo, preemptive = pre, time_quantum = tq)
        pgc.transform(prog, gnt = gnt[i // 2, i % 2], title = algo)
    plt.show(fig)
    
    import pandas as pd
    cpus3 = CPUScheduler(burst_time = [5, 3, 3, 1],
                         arrival_time = [0, 1, 2, 4], 
                         pid = ['P1', 'P2', 'P3', 'P4'])
    prog, summ = cpus3.transform(scheme = 'sjf', preemptive = True, time_quantum = 1)
    print(pd.DataFrame(summ))