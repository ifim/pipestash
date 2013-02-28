# read from stdin, put into queue
# also restart the consumer if it dies for some reason
import sys
import datetime
import signal


def produce(config, queue):
    try:
        def graceful(signum, frame):
            raise Exception("caught {0} signal, exiting".format(signum))

        signal.signal(signal.SIGTERM, graceful)
        signal.signal(signal.SIGINT, graceful)
        signal.signal(signal.SIGQUIT, graceful)

        droppedcount = 0
        firstdropped = None
        while True:
            # read the line
            line = sys.stdin.readline()
            if not line:
                # EOF
                break
            # strip trailing newline
            line = line.rstrip()

            if config.stdout:
                print line

            # toss it in the queue
            try:
                queue.put([datetime.datetime.utcnow().isoformat('T') + 'Z', line])
            except Queue.FULL:
                if not firstdropped:
                    firstdropped = datetime.datetime.utcnow().isoformat('T') + 'Z'
                droppedcount += 1

            if droppedcount:
                try:
                    queue.put([
                        datetime.datetime.utcnow().isoformat('T') + 'Z', 
                        "dropped {0} messages starting at {1} due to full queue".format(droppedcount, firstdropped)
                    ])
                    droppedcount = 0
                    firstdropped = 0
                except Queue.FULL:
                    # queue still full. keep going
                    pass

    except Exception as e:
        print "caught exception {0}, queue length ~{1}".format(e, queue.qsize())
        # FIXME: handle this properly. maybe by putting a message in the queue
        # if there's an uncaught exception besides an interrupt?
        pass

    print "finished putting shit into the queue"
    queue.put(None)
