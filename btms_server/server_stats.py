from datetime import datetime
#from datetime import timedelta
#import atexit
import os
#import sys
import time
import psutil

def get_server_stats():
    def poll(interval):
        # sleep some time
        time.sleep(interval)
        procs = []
        procs_status = {}
        for p in psutil.process_iter():
            try:
                p.dict = p.as_dict(['username', 'nice', 'memory_info',
                                    'memory_percent', 'cpu_percent',
                                    'cpu_times', 'name', 'status'])
                try:
                    procs_status[p.dict['status']] += 1
                except KeyError:
                    procs_status[p.dict['status']] = 1
            except psutil.NoSuchProcess:
                pass
            else:
                procs.append(p)

        # return processes sorted by CPU percent usage
        processes = sorted(procs, key=lambda p: p.dict['cpu_percent'],
                           reverse=True)
        return (processes, procs_status)


    def print_header(procs, procs_status):
        """Print system-related info, above the process list."""
        num_procs = len(procs)

        def get_dashes(perc):
            dashes = "|" * int((float(perc) / 10 * 1))
            empty_dashes = " " * (10 - len(dashes))
            return dashes, empty_dashes

        # cpu usage
        return_list = []
        percs = psutil.cpu_percent(interval=0, percpu=True)
        for cpu_num, perc in enumerate(percs):
            dashes, empty_dashes = get_dashes(perc)
            cpu_usage_nxt = "CPU%-2s [%s%s] %5s%%" % (cpu_num, dashes, empty_dashes,
                                                  perc)
            return_list.append(cpu_usage_nxt)


        # mem
        mem = psutil.virtual_memory()
        dashes, empty_dashes = get_dashes(mem.percent)
        used = mem.total - mem.available
        mem = "Mem   [%s%s] %5s%% %6s/%s" % (
            dashes, empty_dashes,
            mem.percent,
            str(int(used / 1024 / 1024)) + "M",
            str(int(mem.total / 1024 / 1024)) + "M"
        )
        return_list.append(mem)


        # swap usage
        swap = psutil.swap_memory()
        dashes, empty_dashes = get_dashes(swap.percent)
        swap_usage = "Swap  [%s%s] %5s%% %6s/%s" % (
            dashes, empty_dashes,
            swap.percent,
            str(int(swap.used / 1024 / 1024)) + "M",
            str(int(swap.total / 1024 / 1024)) + "M"
        )
        return_list.append(swap_usage)


        # processes number and status
        st = []
        for x, y in procs_status.items():
            if y:
                st.append("%s=%s" % (x, y))
        st.sort(key=lambda x: x[:3] in ('run', 'sle'), reverse=1)
        proc_num = "Processes: %s " % (num_procs)
        proc_stats = "(%s)" % (' '.join(st))

        return_list.append(proc_num)
        return_list.append(proc_stats)

        # load average, uptime
        uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        av1, av2, av3 = os.getloadavg()
        loadaverage = " Load average: %.2f %.2f %.2f " \
            % (av1, av2, av3)
        uptime = "Uptime: %s" \
            % (str(uptime).split('.')[0])

        return_list.append(loadaverage)
        return_list.append(uptime)

        #print cpu_usage, mem, swap_usage, proc_num_stats, la_uptime
        return return_list

    args = poll(0)
    return print_header(*args)

