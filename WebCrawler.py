import socket
import queue
from urllib.parse import urlparse
import threading
import time

class WebCrawler(threading.Thread):

    shared_lock = threading.Lock()
    shared_count = [1]
    def __init__(self, thread_id, name, counter, domain_queue, url_set):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name
        self.counter = counter
        self.domain_queue = domain_queue
        self.shared_count[0] = domain_queue.qsize()
        self.url_set = url_set

    def run(self):
        print("Starting " + self.name)
        self.send(self.domain_queue, self.url_set)
        print("Exiting " + self.name)
        print("------------------------------")

    def send(self, hostname_queue, url_set):

        while True:
            self.shared_lock.acquire()
            if hostname_queue.qsize() < 1:
                self.shared_lock.release()
                break
            try:
                port = 80
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                domain = hostname_queue.get()
                head_request = "HEAD /robots.txt HTTP/1.1\r\nHost: " + domain + "\r\n\r\n"
                get_request = "GET / HTTP/1.1\r\nHost: " + domain + "\r\n\r\n"
                self.shared_count[0]-= 1
                self.shared_lock.release()
                get_host = socket.gethostbyname(domain)
                s.connect((get_host, port))
                s.send(head_request.encode())
                head_response = s.recv(100000).decode('utf-8','ignore')
                head_status_code = head_response.find("HTTP/1.1 200")
                if head_status_code==0:
                    print("200 found in HEAD response!")
                else:
                    print("200 not found in HEAD response")
                    s.send(get_request.encode())
                    get_response = s.recv(100000).decode('utf-8','ignore')
                    get_status_code = get_response.find("HTTP/1.0 200")
                    if get_status_code==0:
                        print("200 found in GET response")
                    else:
                        print("200 not found in GET response")

                s.close()
            except socket.gaierror as gai_error:
                print("Address could not found for host :- "+domain)
                print(gai_error)
            except socket.timeout as time_out_error:
                print("Timeout for host :-  "+domain)
                print(time_out_error)
            except ConnectionResetError as connection_reset_rrror:
                pass
        time.sleep(1)

def main():
    start_time = time.time()
    try:
        file1 = open("URL-input-1K.txt", "r")
        unique_set = set()
        hostname_queue = queue.Queue(maxsize=10000)
        url_set = set()
        for element in file1:
            url = urlparse(element)
            unique_set.add(url.netloc)  # add unique elements to set
            url_set.add(element)

        print("Set Size : ", len(unique_set))
        print("URL Set size : ", len(url_set))

        for i in unique_set:  # add all set elements to queue
            hostname_queue.put(i)

        print("Queue Size : " + str(hostname_queue.qsize()))

    except IOError as error:
        print("No such file"+error)

    list_of_threads = []
    number_of_threads = 100
    for i in range(1, number_of_threads, 1):
        t = WebCrawler(i, "Thread-" + str(i), 10, hostname_queue, url_set)
        t.start()
        list_of_threads.append(t)
    for t in list_of_threads:
        t.join()

    running_time = time.time() - start_time
    print("Running Time is : ", running_time)

if __name__ == '__main__':
    main()
