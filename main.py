#!.env/bin/python3

import argparse
import docker
import os

client = docker.from_env()
dir_path = os.path.dirname(os.path.realpath(__file__))
prefix = "sagi_outbrain_"

def pull_and_deploy(cont_obj: object, master_id=''):
    print('Fetching '+cont_obj.name_tag)
    image = client.images.pull(cont_obj.name_tag)

    print('Deploying '+cont_obj.name_tag)

    if cont_obj.is_master:
        return client.containers.run(
            image.id[7::],
            cont_obj.run_args,
            name=cont_obj.container_name,
            ports=ports,
            volumes=cont_obj.volumes,
            detach=True,
            auto_remove=cont_obj.auto_removal
        )
    return client.containers.run(
        image.id[7::],
        name=cont_obj.container_name,
        volumes=cont_obj.volumes,
        network_mode='container:'+master_id,
        detach=True,
        auto_remove=cont_obj.auto_removal
    )

def stop_required_containers():
    print("Stopping and removing every container that is associated to this project.")
    for cont in client.containers.list():
        if prefix in cont.name:
            cont.stop()

class Container:
    def __init__(self, name: str, version: str, volumes: dict, is_master: bool, auto_removal: bool, run_args: list):
        self.container_name = prefix+name.split("/", 1)[1]
        self.version = version
        self.name_tag = name+':'+version
        self.volumes = volumes
        self.is_master = is_master
        self.auto_removal = auto_removal
        self.run_args = run_args

parser = argparse.ArgumentParser(description='Monitoring-in-a-click')
parser.add_argument(
    '-r',
    '--retention',
    help='Retention in hours',
    metavar='HOURS',
    type=int,
    required=True
)
parser.add_argument(
    '-g', '--grafana-version',
    help='The version of Grafana to deploy',
    metavar='VERSION',
    type=str,
    required=True
)
parser.add_argument(
    '-p',
    '--prometheus-version',
    help='The version of Prometheus to deploy',
    metavar='VERSION',
    type=str,
    required=True
)

args = parser.parse_args()

prom_formatted_ver = args.prometheus_version if args.prometheus_version == 'latest' or args.prometheus_version[0] == 'v' else 'v'+args.prometheus_version

prom_run_args = ['--config.file=/etc/prometheus/prometheus.yml']
#if prom_formatted_ver == 'latest' or (str(prom_formatted_ver[1]) == '2' and int(prom_formatted_ver[3]) > 7):
#    prom_run_args.append('--storage.tsdb.retention.time='+str(args.retention)+'h')
#else:
#    prom_run_args.append('--storage.local.retention='+str(args.retention)+'h')

if prom_formatted_ver == 'latest':
    prom_run_args.append('--storage.tsdb.retention.time='+str(args.retention)+'h')
elif int(prom_formatted_ver[1]) == 2:
    if int(prom_formatted_ver[3]) >= 7:
        prom_run_args.append('--storage.tsdb.retention.time='+str(args.retention)+'h')
    else:
        prom_run_args.append('--storage.tsdb.retention='+str(args.retention)+'h')
else:
    prom_run_args.append('--storage.local.retention='+str(args.retention)+'h')

prom_obj = Container('prom/prometheus', #name
                     prom_formatted_ver, #version
                     {'/etc/prometheus/prometheus.yml':
                      {'bind': dir_path+'/conf/prometheus/prometheus.yml',
                       'mode': 'ro'}
                     }, #volumes
                     True, #is_master
                     True, #Remove on stop
                     prom_run_args  #run_args
)

graf_obj = Container('grafana/grafana', #name
                     args.grafana_version, #version
                     {dir_path+'/conf/grafana/custom.ini':
                      {'bind': '/etc/grafana/custom.ini', 'mode': 'ro'},
                      dir_path+'/conf/grafana/provisioning/':
                      {'bind': '/etc/grafana/provisioning/', 'mode': 'ro'}
                     }, #volumes
                     False, #is_master
                     True, #Remove on stop
                     [] #run_args
)

ports = {'9090/tcp': 9090, '3000/tcp': 3000}

stop_required_containers() #stop and remove all associated containers
prom_cont = pull_and_deploy(prom_obj)
graf_cont = pull_and_deploy(graf_obj, prom_cont.id)

print('You can now access Grafana on http://localhost:3000 and Prometheus on http://localhost:9090')
