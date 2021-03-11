import os
import tempfile

from toil.common import Toil
from toil.job import Job


def helloWorld(message, memory="2G", cores=2, disk="3G"):
    return "Hello, world!, here's a message: %s" % message

if __name__=="__main__":
    options = Job.Runner.getDefaultOptions(tempfile.mkdtemp("tutorial_quickstart")+os.sep+"toilWorkflowRun")
    options.logLevel = "OFF"
    options.clean = "always"

    hello_job = Job.wrapFn(helloWorld, "Woot")

    with Toil(options) as toil:
        print(toil.start(hello_job)) #Prints Hello, world!, ...
