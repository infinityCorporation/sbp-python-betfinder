## To Do for Data Analytics Server

### Current Capabilities:
Currently, the app is able to ingest, analyze, and store data for baseball, basketball, hockey, and football games.
Per run this takes about 14 seconds locally and 3 minutes in the cloud.

### Desired Capabilities: 
We want to be able to store, analyze, and ingest player prop data to allow for a wider range
of sports betting opportunities, namely in the arbitrage sector of our website. 

#### New Architecture Proposal
- Consider adding a new table for player props. The odds API should pass props by player so you can create player rows
- Consider adding a new table for player lines, this should be all player outcomes for a certain prop

The player props are based on the eventId which the player is playing in. This can be 
shown by the endpoint being:

```http request
/sports/{sport}/event/{eventId}/odds?apiKey={}&regions=us&markets={PlayerPropMarket}
```

The NFL Markets we will focus on will be mainly popularity based for the time being. They will be:
player_assists
player_pass_completions
Player_receptions
player_passing_yds
player_rush_yds
player_reception_tds
player_rush_tds

The MLB markets we will focus on will be mainly


#### New Change in the concept:
The player props are based off of the event markets, so they are based off event id. For this, we can simply pull from
the existing all_data table in the database and then create a new row for the