import sys
sys.path.append("./libs/")
import urllib as u
import youtube_dl
import pafy
import soundcloud as sc
import os
import re
import json
import TkTreectrl as treectrl
import tkFileDialog
import thread
from   tabs import *
from   vlc import MediaPlayer
from   HTMLParser import HTMLParser
from   Tkinter import *

cid="50aaa3de7469fde7c1e5e6ad7c91275c"
client=sc.Client(client_id=cid)
parser=HTMLParser()

def searchSC(terms,limit=30):
  tracks=client.get('/tracks',q=terms,filter="public",limit=limit)
  x=[]
  for i in tracks:
    try:
      z={}
      s,ms=divmod(i.fields()['duration'],1000)
      m,s=divmod(s,60)
      h,m=divmod(m,60)
      dur="%d:%02d:%02d" % (h,m,s)
      z["title"]=str(i.fields()['title'])
      z["length"]=dur
      z['url']=str(i.fields()['permalink_url'])
      x.append(z)
    except UnicodeEncodeError:
      pass
  return x

def fetchSC(url,path=os.getcwd()):
  track = client.get('tracks/%s'%(client.get('/resolve', url=url).id))
  stream_url = client.get(track.stream_url, allow_redirects=False)
  f=open(path+"/"+track.title+'.mp3','wb')
  f.write(u.urlopen(str(stream_url.location)).read())
  f.close()
  print "Done"

def searchYT(terms,limit=30):
  results=[]
  page=1
  x=[]
  while len(results)<=limit:
    query_string = u.urlencode({"search_query" : terms,"page" : page})
    html = u.urlopen("http://www.youtube.com/results?" + query_string).read()
    search_results = re.findall(r'href\=\"\/watch\?v\=(.{11})',html)
    for i in search_results:
      if not results.__contains__(i):
        try:
          results.append(i)
          html=html.split('<h3 class="yt-lockup-title "><a href="/watch?v=',1)[1]
          url,html=html.split('" ',1)
          html=html.split('"  title="',1)[1]
          title,html=html.split('" ',1)
          html=html.split('Duration: ',1)[1]
          dur,html=html.split('.<',1)
          dur=dur.split(":")
          if len(dur)!=3:
            dur=[0,int(dur[0]),int(dur[1])]
          else:
            z=[]
            for i in dur:
              z.append(int(i))
            dur=z
          h,m,s=dur
          title=str(parser.unescape(title))
          x.append({'title':title,'length':"%d:%02d:%02d"%(h,m,s),'url':url})
        except:
          pass
    page+=1
  return x

def fetchYT(ident,path=os.getcwd()):
  try:
    v=pafy.new("http://www.youtube.com/watch?v="+ident)
  except:
    v=pafy.new("http://www.youtube.com/watch?v="+ident)
  audio=v.getbestaudio()
  audio.download(path,True)
  if str(audio).find("mp3")==-1:
    os.system("ffmpeg -i '%s' -codec:a libmp3lame -qscale:a 2 '%s.mp3'"%(
      path+"/"+str(v.title)+"."+str(audio).split(":",1)[1].split("@",1)[0],path+"/"+str(v.title)))
    os.system('rm "%s"'%(path+"/"+str(v.title)+"."+str(audio).split(":",1)[1].split("@",1)[0]))
  print "Done"

def doSearch(event,query=None):
  global urls
  urls=[]
  if event!=None:
    query=event.widget.get()
  if query!='':
    searches=searchYT(query)+searchSC(query)
    lbox.delete(0,END)
    for i in searches:
      lbox.insert(END,i['title'],i['length'])
      urls.append(i['url'])
    return urls

def playAudio(url):
  global mp,oldUrl
  if url==oldUrl:
    mp.play()
  else:
    if len(url)==11:
      try:
        mp.stop()
      except:
        pass
      try:
        v=pafy.new(url)
        v=v.getbestaudio()
        mp=MediaPlayer(v.url)
        mp.play()
      except:
        v=pafy.new(url)
        v=v.getbestaudio()
        mp=MediaPlayer(v.url)
        mp.play()
    else:
      track = client.get('tracks/%s'%(client.get('/resolve', url=url).id))
      stream_url = client.get(track.stream_url, allow_redirects=False)
      try:
        mp.stop()
      except:
        pass
      mp=MediaPlayer(str(stream_url.location))
      mp.play()
    oldUrl=url

def pauseAudio():
  global mp
  mp.pause()

def doDL(url):
  if len(url)==11:
    thread.start_new_thread(fetchYT,(url,))
  else:
    thread.start_new_thread(fetchSC,(url,))

def setDLPath():
  global dlpath
  dlpath=tkFileDialog.askdirectory()
  os.chdir(dlpath)
  savepath.config(text="Save Path:    "+dlpath)

urls=[]
w=Tk()
oldUrl=''
main=LabelFrame(w)
PLAY=PhotoImage(master=w,file='img/playButton.gif')
PAUSE=PhotoImage(master=w,file='img/pauseButton.gif')
DOWNLOAD=PhotoImage(master=w,file='img/downloadButton.gif')
w.title("Muzez Client")
w.geometry("808x665")
lbox=treectrl.MultiListbox(main)
search=Entry(main)
search.config(width=75)
search.focus()
search.grid(row=1,column=1)
search.bind("<Return>",func=doSearch)
pb=Button(main,command=lambda:playAudio(urls[lbox.selection_get()[0]-1]))
pb.config(image=PLAY,width=23,height=23)
pb.grid(row=1,column=3)
pbt=Button(main,command=lambda:pauseAudio())
pbt.config(image=PAUSE,width=23,height=23)
pbt.grid(row=1,column=4)
db=Button(main,command=lambda:w.after(1,doDL(urls[lbox.selection_get()[0]-1])))
db.config(image=DOWNLOAD,width=23,height=23)
db.grid(row=1,column=5)
lbox.config(columns=('Title','Duration'),width=800,height=600)
lbox.grid(row=3,column=1,columnspan=5,sticky='nesw')

submit=Button(main,text="Search",command=doSearch(None,query=search.get())).grid(row=1,column=2)
savepath=Label(main,text="Save Path:    "+os.getcwd())
savepath.grid(row=2,column=1,columnspan=1)
Button(main,text='Browse', command=setDLPath).grid(row=2,column=2,columnspan=1)
main.grid(row=1,column=1)
w.mainloop()
