import matplotlib.pyplot as plot
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from functools import partial

general_channels = [988202173760405557, 991016201813626880]
help_channels = [988498937793105920, 988498938782953532, 988498939818934272]

Past_Days = 10
Max_Users = 10

def get_member_from_id(guild, i):
    member = guild.get_member(i)
    return member.name if member else np.nan

# Thanks To Yann For This Chaining Style Processing <3
df = pd.read_csv('user_data.csv', names=['Ch_ID', 'Usr_ID', 'Time'])
df = (df
  .assign(Time=pd.to_datetime(df['Time'], unit='s'))
  .loc[ lambda x: x['Time'] > datetime.now() - timedelta(days=10) ]
  .groupby(['Ch_ID', 'Usr_ID'], as_index=False).size()
  .sort_values('size', ascending=False)
  .rename(columns={'size': 'Count'}))

general_users = (df
  .loc[ lambda x: x['Ch_ID'].isin(general_channels) ]
  .assign(Usr_ID= df['Usr_ID'].apply(lambda x: partial(get_member_from_id, guild)))
  .rename(columns={'Usr_ID': 'Name'})
  .dropna()
  .head(Max_Users))

help_users = (df
  .loc[ lambda x: x['Ch_ID'].isin(help_channels) ]
  .assign(Usr_ID= df['Usr_ID'].apply(lambda x: partial(get_member_from_id, guild)))
  .dropna()
  .rename(columns={'Usr_ID': 'Name'})
  .head(Max_Users))

print(general_users)
print(help_users)
