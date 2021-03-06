dockit is a command-line tool which allows to capture system calls made by a process or a process tree.

It is a Python script which runs the target process under control of the famous strace or ltrace Linux commands. It creates, for each run:
* A txt file where the system calls are aggregated into bigger logical blocks.
* A summary XML file containing all process, files and sockets created
* A Dockerfile and the associated directory, to create a Docker image,
* Also, a raw log file containing the system calls, which allows to rerun the test.

It is a standalone script, compatible with Python 2 and Python 3. For the moment,
it works on Linux only. Porting to Microsoft Windows is planned.
It is also possible to port it to other Linux flavours.

How does it work:
=================

The script runs a command, or attaches to a process id, and reads the input produced by strace/ltrace, which produces a lot of information, which cannot be directly used. This log of system calls is then processed to produce a synthetic information.

Command line options:
=====================
dockit.py -h

Loaded packages cache file:FileToPackageCache.vps516494.localdomain.txt
DockIT: ./dockit.py <executable>
Monitors and factorizes systems calls.
  -h,--help                     This message.
  -v,--verbose                  Verbose mode (Cumulative).
  -w,--warning                  Display warnings (Cumulative).
  -s,--summary <CIM class>      Prints a summary at the end: Start end end time stamps, executable name,
                                loaded libraries, read/written/created files and timestamps, subprocesses tree.
                                Examples: -s 'Win32_LogicalDisk.DeviceID="C:",Prop1="Value1",Prop2="Value2"'
                                          -s 'CIM_DataFile:Category=["Others","Shared libraries"]'
  -D,--dockerfile               Generates a dockerfile.
  -p,--pid <pid>                Monitors a running process instead of starting an executable.
  -f,--format TXT|CSV|JSON      Output format. Default is TXT.
  -F,--summary-format TXT|XML   Summary output format. Default is XML.
  -i,--input <file name>        trace command input file.
  -l,--log <filename prefix>    trace command log output file.
  -t,--tracer strace|ltrace|cdb command for generating trace log

Examples:
=========

This list some examples, with the strace or ltrace commands internally created and. It is always possible to run thees commands separately, and feed dockit with it, in replay mode. All examples are documented in the ini files. Typical strace or ltrace commands are:

Command "ls" with strace:
-------------------------
The default trace program is strace.

dockit.py ls
strace -q -qq -f -tt -T -s 200 -y -yy -e trace=desc,ipc,process,network,memory ls

Attaching to process 4233:
--------------------------
dockit.py -p 4233
strace -q -qq -f -tt -T -s 200 -y -yy -e trace=desc,ipc,process,network,memory -p 4233

Command "ps", traced with ltrace:
---------------------------------
The command-line option -t allows to choose a tracer command.
dockit.py -t ltrace ps -ef
ltrace -tt -T -f -S -s 200 -e -*+getenv+*@SYS ps -ef

Command "netstat". Stores the result:
-----------------------------------

dockit.py -l XYZ -t ltrace netstat
ltrace -tt -T -f -S -s 200 -e -*+getenv+*@SYS netstat

This generates several files:
XYZ.ltrace.29765.ini Contains the parameters to rerun this session.
XYZ.ltrace.29765.log All the logged system calls.
XYZ.ltrace.29765.txt Aggregated system calls.

Replay a session, and generates a Dockerfile:
---------------------------------------------
dockit.py -i XYZ.ltrace.29765.log -D

find docker.docker/ -ls
drwxrwxr-x  4096 May  8 22:53 docker.docker/
-rw-rw-r--   764 May  8 22:53 docker.docker/Dockerfile

This Dockerfile can be used to create a Docker image.

Run a session, create a summary file and a Dockerfile:
------------------------------------------------------

./dockit.py -l ABC -F XML -D grep xyz '*.py'
strace -q -qq -f -tt -T -s 200 -y -yy -e trace=desc,ipc,process,network,memory grep xyz *.py

This generates the files:
ABC.strace.29887.ini Session parameters.
ABC.strace.29887.log All system calls.
ABC.strace.29887.txt Aggregated system calls.
ABC.strace.29887.xml Summary of all resources.
ABC.strace.29887.docker:
    Dockerfile



Next steps:
===========

Survol ?
--------
Survol is an interactive tool for analysing and exploring a computer system. 
It extracts and displays managed elements in an IT environment, represented in the Common Information Model (CIM) open standard as a common set of objects and relationships between them.

The elements extracted by DockIT can be displayed by Survol, along with other information.
Both tools are orthogonal: DockIT brings to Survol its temporal dimension,
as opposed to Survol snapshots.

To interface DockIT and Survol, DockIT starts a HTTP server displaying the same objects as the Survol scripts,
fetched from its internal cache of objects.
It is then up to the browser to connect to a more general Survol browser.

Another approach is to have Survol scripts which will access a running DockIT script,
or start one. This can work to monitor a running process, but cannot work when an entire
system is being monitored as a whole, running specific commands in a specific environment.

A technical possibility was to use Python interprocess queues. Python processes (Such as started by WSGI)
would write CIM elements creations, updates or deletes in these queues which would be read
by the HTTP server, from a script. The role of the script would simply be to start a data 
server if need be, then read data from the queue.

DockIT would then be one type of data server: It would work as now, but:
- Without files generation (Log, summary, Dockerfile).
- Writing elements create, update or delete events to the queue.

User libraries calls:
---------------------
At the moment, only system calls are analysed although ltrace allows to trace
any shareable library.
A specific module should probably be created per library.

Mysql:
------
This is an example of a library whose communication protocol can be reverse-engineered:
System calls as found in the log file:
; sendto(127.0.0.1:3306]>, "\21\0\0\0\3set autocommit="
; sendto(127.0.0.1:3306]>, "\n\0\0\0\3use mysql"
; sendto(127.0.0.1:3306]>, "\f\0\0\0\3show tables"
; sendto(127.0.0.1:3306]>, "\33\0\0\0\3select Host,Use"

We can parse the content (Which some utility tools creayed for Survol)
and create tables etc... in the XML file.

Oracle:
-------
; write(6<pipe:[5648149]>, "...0\0\0\0\0\0'select username, user_id from"..., 312) = 312 <0.000016>


Port to Microsoft Windows:
--------------------------
Apparently, there is no tool similar to ltrace or strace.
The solution is to use the existing module pygdb:
- Port to Python3 (Using pygdb3)
- Remove what is not needed (PE, pydasm)

Notification of created processes:
----------------------------------

There is a need to track the unexpected creation of processes.
Suggestion to notify the creation of processes from a given user or group,
adding the command-line options:
 -u --user
 -g --group

Information here about linux process monitoring (exec, fork, exit, set*uid, set*gid)
http://bewareofgeek.livejournal.com/2945.html
https://stackoverflow.com/questions/26852228/detect-new-process-creation-instantly-in-linux
https://stackoverflow.com/questions/6075013/detect-launching-of-programs-on-linux-platform
 
It is also possible (desirable ?) to track creation of files in a given directory,
and monitor the processes accessing them:
https://www.eventtracker.com/newsletters/how-to-use-process-tracking-events-in-the-windows-security-log/
https://pypi.python.org/pypi/inotify


More efficiency, less storage, with a data window:
--------------------------------------------------
At the moment, all intermediate data are stored into memory, and used
at script's end, when various files are created.

It would be more efficient to store data in a small window, a circular buffer.
This would allow to monitor an application without limitation
of time and space.

More data aggregation:
----------------------

At the moment, system calls are aggregated in another output file,
strongly reducing its size, for the same synthetic information.
It is possible to go further into this direction
to give a better overview of what a program is really doing:
- Extracts the valuable inforation moved in IOs (SQL queries, any data ...)
- Separate distinct processing streams, based on different pids, threads,
and processing peaks; the goal being to apply processing mining techniques
to streams of instructions.
 
Machine learning:
-----------------
scikit-learn module provide simple and efficient tools for data mining and data analysis,
notably for classification, clustering, feature extraction etc...

Consider running sklearn on the window, so that not the whole history is necessary.
Machine learning with any output data of the program:
- File content.
- Screen hard-copy.
- etc...
Predict next calls ?

The plan is to apply these techniques on the aggregated calls,
in order to enhance the software understanding, by:
- Isolating logical steps
- Detecting common patterns
- Qualifying streams of processing will well-known activities.

(1) The aggregated system calls can be transformed into free text describing the running operations:
System calls - possibly grouped, parameters, buffers content.
This contains only the interaction of the system with the outside world.
Only a sliding window of system calls - possibly aggregated - is enough.
This can be associated with other data coming from the program: Graphic display,
network operations, database operations etc...
Usage: Gives the hint about what the system is doing. Example:
- Dialog on a socket.
- ...

(2) The user can provide a CSV file with tags as output. Use that for learning before classification
of read() and write() buffers. Resulting tags stored in XML file.
When it matches, the Python module is called with these data, and do things like:
- Return CIM-like objects
- Process mining.
Usage: Gives a hint about data files with category="Others".
Not needed for well-known files, such as libraries, sqlite etc....

(3) Find a correlation between the content of several simultaneous streams.
Usage: ???
- Model the process as a black box ? Really too far. An internal state should be used.
Makes no sense when it is data manipulation.



Analysing the content of buffers just to classify them is not really interesting.
What we want to do is extract CIM objects (for Survol) and cases ids (For process mining).
But thees two domains need text data only.
Therefore, there is not point using binary samples of buffers, because they will need to be converted anyway.

In the very important case if SQL, one socket direction might be easily analysed (SQL queries),
but not the opposite direction. Although it can only contain data, possibly in CSV format.


Process mining:
---------------
Process mining is a family of techniques in the field of process management
that support the analysis of business processes based on event logs.
It is required that the event logs data be linked to a case ID, activities, and timestamps.

The goal is to extract or synthetize case ID and activities from the system calls log files,
to result in models describing business processes.

Process mining techniques are able, with such logs,
to extract patterns, details etc...

What is only needed is to transform the system calls logs into triplets of:
Case id, activity and time stamp.

For this framework to be applicable, technical resources have to be considered
as being part of the resources of the company, and are the at the lowest level of the business processes.

The technical resources are related in some way with the higher-level business objects.
The difficulty is that this relation is not documented, or not one-to-one.
The goal is to discover this relation between the technical objects in call logs,
and the business objects, whose processing yields these call logs.
This association is an iterative process, potentially helped by a user.

Consider text method from sklearn, to detect and extract case ids:
- A case id is a "rare" string occuring in several streams frames.
- It can be a group of rare strings: First name, surname etc...
strongly correlated.
- Different caseids should not appear together in the same frame of a stream.

In a stream, remove the words which are always part of this category of streams.
For example, in SQL, remove the SQL keywords.
What is left are case ids, or data specific to the case.
Plus, of course, time-stamps, counters etc...

If it is not possible to split a stream based on time stamps, or io buffers,
then detect periodic patterns. Ex:
insert into XXX value("a");insert into XXX value("bb");insert into XXX value("ccc");
Just extract "a","bb","ccc".
Consider Markov chains.

If a segment is "not too big", calculate Levenshtein distance with "a couple of previous" segments,
this distance being stored in a distance matrix.
The goal is to create clusters of "similar" segments.
Store the first N segments, calculate their Levenshtein distance matrix,
for the first N segments.
the n selects the "center" of each cluster. Only the centers are kept.
http://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html
https://en.wikipedia.org/wiki/N-gram

Example of application: Analysing the content of a socket to a database engine.
This does not work with stored procedures.
This socket transports SQL queries of a couple of different types: "select from a", "insert into b" etc...
This is typical of programs always running the same set of queries,
with bind variables and substitution.
We want to:
(1) Extract the variables which are the case id for process mining.
(2) Extract the table names to investigate dependencies.
This should apply to the returned values, even if the keywords are only delimiters.

So we have an object which is fed with the incoming queries.
It clusterizes them.
It can give the skeleton of each cluster,
the inverse of variables subsitution.
If it receives a very big buffer, it is able to detect periodic patterns.
https://en.wikipedia.org/wiki/Anti-unification_(computer_science)
https://en.wikipedia.org/wiki/Grammar_induction

Splitting into tokens is specific to the language:
Which delimiters, if delimiters are escaped etc...
However, we can assume some generic rules.

This is an independant package.
dockit uses it if it is there only.

class induction_engine:
    void add_sample(string qry)

    // Each string of the form "insert into ABC values(\1,\2)" or whatever placeholder.
    list<string> clusters()

    int cluster_id(string qry)
    list<string> extract_substitution_variables(string qry)

// This may use the patterns induced.
// But maybe we cannot.
class detect_periodic_patterns:

To ease development, we can create a mock object which just stores the data for later
processing and testing. This helps creating realistic data sets.
Results:
- No clusters detected.
- No substitution variables (aka case id) detected.

scipy.sparse
