#Import everything
import os
import time
from discord.ext import commands
from keep_alive import keep_alive
from replit import db
from datetime import datetime, date, timedelta
import math
import gspread
import json
import ast

#Connecting to Google Sheets API
#Replace with actual json file
mystring = os.environ['json']
my_dict = ast.literal_eval(mystring)
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(my_dict, f, sort_keys = True, ensure_ascii=False, indent=4)
sa = gspread.service_account(filename = 'data.json')
sh = sa.open("Stat_Sheets")
wks = sh.worksheet("Data")
print('Rows: ', wks.row_count)
print('Columns: ', wks.col_count)
os.remove('data.json')

#Date when the bot started
startdate = date.today()
cell = (int(str(date.today()+timedelta(days=2)-startdate).split()[0]))


#Debug. Prints today's date into console
print(str(date.today()))

#Global variable which is needed for leveling up. Each level is twice the basexplimit
basexplimit = 1000

#Delete quotation marks to reset every stat manually
"""
db["sxp"] = 0
db["jxp"] = 0
db["axp"] = 0
db["mxp"] = 0
db["slvl"] = 1
db["jlvl"] = 1
db["alvl"] = 1
db['mlvl'] = 1
"""

#Returns date in correct format for G Sheets
def changedate():
  day =str(date.today())
  return '=DATE(' + day.replace("-",",") + ')'

#Bot uses $ sign for commands
client = commands.Bot(command_prefix = '$')

#Blueprint for all skills
class Subject:
  def __init__(self,name,code,xp,lvl):
    self.name = name
    self.code = code
    self.xp = xp
    self.lvl = lvl
    self.days = date.today()
    self.dayl = date.today()
  #Whenever a task is completed
  def complete(self):
    global basexplimit, boolcodes
    #Sets the date if null
    if wks.acell(f'A{cell}').value == None:
      wks.update(f'A{cell}',changedate(), raw = False)
    #Value must not be inserted yet
    if wks.acell(f'{self.code[0]}{cell}').value == None:
      #Checks for unrecorded data and sets fails
      if wks.acell(f'{self.code[0]}{cell-1}').value == None:
        for c in range(cell-1):
          if wks.acell(f'{self.code[0]}{c+1}').value == None:
            wks.update(f'A{c+1}',f'{changedate()}-{cell-c-1}', raw = False)
            wks.update(f'{self.code[0]}{c+1}', 'Failed')
      reply = ""
      try:
        #Deducts xp if overdue
        if int(str(date.today()-self.dayl).split()[0]) > 2:
          self.xp-=20*self.lvl*int(str(date.today()-self.dayl).split()[0])
          reply = f"Congratulations on completing {self.name} excercise! Unfortunately, I have to deduct "+ str(20*self.lvl*int(str(date.today()-self.dayl).split()[0])-10) + f" {self.name} xp, because there have been no logs for {str(date.today()-self.dayl).split()[0]} days... but... I am glad to see you return! It's time to make a comeback!"
          self.xp+=10
          self.days = date.today()
      except:
        self.xp+=10
        try:
          #Checks if there's a streak and grants bonus xp
          if int(str(date.today()-self.days).split()[0]) > 3 and int(str(date.today()-self.days).split()[0]) < 20:
            self.xp += 1*int(str(date.today()-self.days).split()[0])
            reply = "You're on " + str(date.today()-self.days).split()[0] + " days streak! Keep it up! " + str(1*int(str(date.today()-self.days).split()[0])+10) + f" {self.name} xp has been added to your character!"
          #Checks if the limit has been hit
          elif int(str(date.today()-self.days).split()[0]) >= 20:
            self.xp += 20
            reply = "You're on " + str(date.today()-self.days).split()[0] + f" days streak! Keep it up! 30 {self.name} xp (limit) has been added to your character!"
          else:
              reply = f"Well done! 10 {self.name} xp has been added to your character!"
        #I don't know if anything can go wrong, but I will leave it here
        except:
          reply = f"Well done! 10 {self.name} xp has been added to your character!!"
      self.dayl = date.today()
      #Checks for level ups level downs
      if self.xp>=basexplimit*self.lvl:
        self.xp-=basexplimit*self.lvl
        self.lvl+=1
      elif self.xp<0:
        self.lvl-=1
        self.xp+=basexplimit*self.lvl
      wks.update(f'{self.code[0]}{cell}','Completed')
      wks.update(f'{self.code[1]}2',self.xp)
      wks.update(f'{self.code[2]}{cell}',self.xp+basexplimit*(self.lvl-1))
      wks.update(f'{self.code[3]}2',self.lvl)
    else:
      return f"You have already completed this today. Come back tomorrow!"
    
    return reply
  #Shows stats
  def stat(self):
    return f'**{self.name}** - Level {self.lvl} [{self.xp}/{basexplimit*self.lvl}] ({math.floor(self.xp/(basexplimit*self.lvl)*100)}%)\n'
  #Save stats
  def save(self):
    db[self.name[0].lower()+"xp"] = self.xp
    db[(self.name[0]).lower()+"lvl"] = self.lvl
  #Resets every stat
  def reset(self):
    self.xp = 0
    self.lvl = 1
    self.days = date.today()
    self.dayl = date.today()

csport = Subject("Sport",['B','C','D','E'], db['sxp'],db['slvl'])
cjapanese = Subject("Japanese", ['F','G','H','I'], db['jxp'],db['jlvl'])
canalytics = Subject("Analytics", ['J','K','L','M'], db['axp'],db['alvl'])
cmental = Subject("Mental", ['N','O','P','Q'], db['mxp'],db['mlvl'])

#When bot starts
@client.event
#when the bot starts
async def on_ready():
  print('Ganyu is ready!')

#Shows stats
@client.command(pass_context = True)
async def stats(ctx):
  await ctx.send(csport.stat()+cjapanese.stat()+canalytics.stat()+cmental.stat())
  time.sleep(1)
  await ctx.send("You're doing great! Keep ut up!")

@client.command(pass_context = True)
async def reset(ctx):
  csport.reset()
  cjapanese.reset()
  canalytics.reset()
  cmental.reset()
  await ctx.send("Got it. Resetting everything...")

@client.command(pass_context = True)
async def save(ctx):
  csport.save()
  cjapanese.save()
  canalytics.save()
  cmental.save()
  await ctx.send('Every stat has been successfully saved')

@client.command(pass_context = True)
async def sport(ctx):
  await ctx.send(csport.complete())

@client.command(pass_context = True)
async def japanese(ctx):
  await ctx.send(cjapanese.complete())

@client.command(pass_context = True)
async def analytics(ctx):
  await ctx.send(canalytics.complete())

@client.command(pass_context = True)
async def mental(ctx):
  await ctx.send(cmental.complete())

@client.command(pass_context = True)
async def greeting(ctx):
  await ctx.send("Hi! I am bot Ganyu!")

#List of features to implement. Notes can be made via Discord
@client.command(pass_context = True)
async def features(ctx):
  await ctx.send(f"Oh, yes. The list of features that you wanted to implement. It should be somewhere here...")
  time.sleep(3)
  features = ""
  count = 1
  for thing in db["feature_list"]:
    features += f'{count}) '
    features+=thing
    features+='\n'
    count+=1
  await ctx.send(f"{features}")
  time.sleep(4)
  await ctx.send(f"I believe that is everything that you wanted. If you have anything else you would like to implement, I can write it down")

#Add a feature to the list
@client.command(pass_context = True)
async def addfeature(ctx, *message):
  feature = str(message)[1:-1]
  featurelist = feature.split(" ")
  feature = ""
  for thing in featurelist:
    if featurelist.index(thing) == len(featurelist)-1:
      feature+=thing[1:-1]
      break
    feature+=thing[1:-2]
    feature+=" "
  db["feature_list"].append(feature)
  await ctx.send(f'Added a feature named "{feature}"!')

#Delete a feature from the list
@client.command(pass_context = True)
async def delfeature(ctx, *message):
  message = int(str(message)[2:-3])
  await ctx.send(f'All right, removing "{db["feature_list"].pop(message-1)}" from the list!')  


#The bot is running in repit. This keeps replit from shutting down the bot.
keep_alive()
#Replace with Discord Bot Token
client.run(os.environ['Token'])