from flask import Flask, url_for, request
from flask_request_params import bind_request_params
import yaml
import requests
import docker
import json
import socket
import time
from subprocess import call

app = Flask(__name__)
adapter_dict = {"adapters":[]}
# port_server = 8080
# master_ip = '192.168.1.151'


# slice_id, slice_part_id e namespace sao passados como argumentos
@app.route('/listPods', methods = ['POST']) 
def list_pods():
    post_data = request.data.decode('utf-8') # exemplo de data: "Telemarketing, slice-part-test-01, espaco-testes"
    post_data = post_data.split(', ')    
    # print(data)

    for adapter_iterator in adapter_dict['adapters']:
        if adapter_iterator['slice-id'] == post_data[0]:
            for slice_part_it in adapter_iterator['parts']:
                if slice_part_it['slice_part_id'] == post_data[1]:
                    

            # resp = requests.get("http://" + master_ip + ":" + str(port) + "/api/v1/namespaces/" + data['namespace'] + "/pods/")
            resp = requests.get("http://0.0.0.0:" + adapter_iterator['port'] + "/listPods")
            parsed = json.loads(resp.content)
            print(json.dumps(parsed, indent=2))
            return 'OK'
    return 'Adapter not found'

@app.route('/listPods', methods = ['GET']) 
def list_all_pods():
    data = request.data.decode('utf-8')
    print(data)
    for i in adapter_dict['adapters']:
        resp = requests.get("http://0.0.0.0:" + str(i['port']) + "/listPods")
        parsed = json.loads(resp.content)
        print(json.dumps(parsed, indent=2))
    return 'OK'

def start_slice_adapter(json_content):
    global adapter_dict
    
    #Start container for the IMA Agents/Adapters
    adapter_dict["adapters"].append({"slice-id":json_content['slice-id'],"parts":[]})

    for i in json_content['dc-slice-part']:
        slice_name = i['name']
        slice_user = i['user']
        agent_name = slice_name + '_' + slice_user + '_agent'
        # print ('Nome da slice:' + str(slice_name))

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('localhost', 0))
        port = s.getsockname()[1]
        s.close()
        # SALVAR: slice_part_id, slice port
        ######## slice-part-test-01, espaco-teste, nginx -> CHAMADA DE UM /getPod
        for j in i['vdus']: 
            if str(j['dc-vdu']['type']) == "master":
                temp_ip = str(j['dc-vdu']['ip-address']) # identifica o mestre e salva o ip nessa string
                temp_port = str(j['dc-vdu']['port'])

        client = docker.from_env()
        client.containers.run("agentwill:latest", detach=True, name=agent_name, ports={'1010/tcp': ('localhost', port)})
        print("http://0.0.0.0:" + str(port) + "/setIPandPort")
        time.sleep(3)
        master_data = temp_ip + ":" + temp_port
        for k in adapter_dict['adapters']:
            # print(k)
            if k['slice-id'] == json_content['slice-id']:
                k['parts'].append({"slice_part_id":slice_name,"adapter_name":agent_name,"port":str(port)})
        # adapter_dict["adapters"].append({"slice_part_id":slice_name,"adapter_name":agent_name,"port":str(port)})

        # print(json.dumps(adapter_dict, indent=2))

        requests.post("http://0.0.0.0:" + str(port) + "/setIPandPort", data = master_data)
        print("The Adapter", agent_name, "has started")

    # adapter_dict["adapters"].append(})

@app.route('/')
def default_options():
    return 'Welcome to Resource and VM Management of IMA!'

@app.route('/listAdapters', methods = ['GET'])
def list_adapters():
    print(json.dumps(adapter_dict, indent=2))
    return 'OK'

@app.route('/deleteAdapter', methods = ['POST'])
def delete_adapter():
    data = request.data.decode('utf-8')
    print(data)
    for i in adapter_dict['adapters']:
        if i['slice_part_id'] == data:
            client = docker.from_env()
            container = client.containers.get(i['adapter_name'])
            container.stop()
            container.remove()
            del i['slice_part_id']
            return 'OK'
    return 'Adapter not found'

@app.route('/startManagementAdapter', methods = ['POST'])
def start_monitoring():
    #print(request.headers)
    file_name = request.data.decode('utf-8')
    print(file_name)
    file = open(file_name, "r")
    yaml_content = file.read()
    file.close()

    json_content = json.dumps(yaml.safe_load(yaml_content))
    json_content = json.loads(json_content)
    # slice_id = json_content['slice']['id']

    start_slice_adapter(json_content)
    return 'OK'

@app.route('/stopManagementAdapter')
def stop_monitoring():
    return 'Stopping the Resource and VM Management infrastructure'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5001')




#TODO
#- deletar adapters
#- salva adapter no fim da execucao
#- yaml ou string?