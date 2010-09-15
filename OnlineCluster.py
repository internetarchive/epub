#!/usr/bin/env python 

# You may have this code under the 
# Do What The Fuck You Want To Public License 
# http://sam.zoy.org/wtfpl/

# Some more info is at:
# http://gromgull.net/blog/2009/08/online-clustering-in-python/

import sys
import math
import heapq
import operator
import random

# we need scipy
#import scipy
import numpy
scipy = numpy


# def kernel_linear(x,y):
#     return scipy.dot(x,y)

# def kernel_poly(x,y,a=1.0,b=1.0,p=2.0):
#     return (a*scipy.dot(x,y)+b)**p

def kernel_gauss(x,y, sigma=0.00001):
    v=x-y
    l=math.sqrt(scipy.square(v).sum())
    return math.exp(-sigma*(l**2))

def kernel_normalise(k): 
    return lambda x,y: k(x,y)/math.sqrt(k(x,x)+k(y,y))

kernel=kernel_normalise(kernel_gauss)

def kernel_dist(x,y):
    # if gaussian kernel:
    return 2-2*kernel(x,y)
    # if not
    #return kernel(x,x)-2*kernel(x,y)+kernel(y,y)

class Cluster(object):
    def __init__(self, a): 
        self.center=a
        self.size=0
        
    def add(self, e):
        self.size+=kernel(self.center, e)
        self.center+=(e-self.center)/self.size
        
    def merge(self, c):        
        self.center=(self.center*self.size+c.center*c.size)/(self.size+c.size)
        self.size+=c.size

    def resize(self,dim):
        extra=scipy.zeros(dim-len(self.center))
        self.center=scipy.append(self.center, extra)
        
    def __str__(self):
        return "Cluster( %s, %f )"%(self.center, self.size)

class Dist(object):
    """this is just a tuple,
    but we need an object so we can define cmp for heapq"""
    def __init__(self,x,y,d):
        self.x=x
        self.y=y
        self.d=d
    def __cmp__(self,o):
        return cmp(self.d,o.d)
    def __str__(self):
        return "Dist(%f)"%(self.d)

class OnlineCluster(object) : 
    def __init__(self, N):
        """N-1 is the largest number of clusters I can find
        Higher N makes me slower"""
        
        self.n=0
        self.N=N
                
        self.clusters=[]
        # max number of dimensions we've seen so far
        self.dim=0 

        # cache inter-cluster distances
        self.dist=[]

    def resize(self, dim):
        for c in self.clusters:
            c.resize(dim)
        self.dim=dim
        
    def cluster(self, e):

        if len(e)>self.dim:
            self.resize(len(e))
                            
        if len(self.clusters)>0: 
            # compare new points to each existing cluster
            c=[ ( i, kernel_dist(x.center, e) ) for i,x in enumerate(self.clusters)]
            closest=self.clusters[min( c , key=operator.itemgetter(1))[0]]
            closest.add(e)
            # invalidate dist-cache for this cluster
            self.updatedist(closest)

        if len(self.clusters)>=self.N and len(self.clusters)>1:
            # merge closest two clusters
            m=heapq.heappop(self.dist)
            m.x.merge(m.y)
            
            try:
                self.clusters.remove(m.y)
            except ValueError:
                pass
            self.removedist(m.y)
            
            self.updatedist(m.x)

        # make a new cluster for this point
        newc=Cluster(e)
        self.clusters.append(newc)
        self.updatedist(newc)
        
        self.n+=1
    
    def removedist(self,c):
        """invalidate intercluster distance cache for c"""
        r=[]
        for x in self.dist:
            if x.x==c or x.y==c: 
                r.append(x)
        for x in r: self.dist.remove(x)
        heapq.heapify(self.dist)
        
    def updatedist(self, c):
        """Cluster c has changed, re-compute all intercluster distances"""
        self.removedist(c)

        for x in self.clusters:
            if x==c: continue
            d=kernel_dist(x.center,c.center)
            t=Dist(x,c,d)
            heapq.heappush(self.dist,t)
                
    def trimclusters(self):
        """Return only clusters over threshold"""
        t=scipy.mean([x.size for x in filter(lambda x: x.size>0, self.clusters)])*0.1
        return filter(lambda x: x.size>=t, self.clusters)
    
    
if __name__=="__main__": 
    
    import random
    import time
    try:
        import pylab
        plot=True
    except:
        plot=False

    points=[]
    # create three random 2D gaussian clusters
    var = .05
    for i in range(3):
        x=random.random()*3
        y=random.random()*3
        c=[scipy.array((x+random.normalvariate(0,var), y+random.normalvariate(0,var))) for j in range(100)]
        points+=c

    var = .95
    x=random.random()*3
    y=random.random()*3
    c=[scipy.array((x+random.normalvariate(0,var), y+random.normalvariate(0,var))) for j in range(10)]
    points+=c
    
    if plot: pylab.scatter([x[0] for x in points], [x[1] for x in points])

    random.shuffle(points)
    n=len(points)

    start=time.time()
    # the value of N is generally quite forgiving, i.e.
    # giving 6 will still only find the 3 clusters.
    # around 10 it will start finding more
    c=OnlineCluster(6)
    while len(points)>0: 
        c.cluster(points.pop())

    clusters=c.trimclusters()
    print "I clustered %d points in %.2f seconds and found %d clusters."%(n, time.time()-start, len(clusters))

    if plot: 
        cx=[x.center[0] for x in clusters]
        cy=[y.center[1] for y in clusters]
    
        pylab.plot(cx,cy,"ro")
        pylab.draw()
        pylab.show()
