import os 
os.environ['DISABLE_SCHEDULER']='1' 
from scripts.crawlers.pl_players import PLPlayersCrawler 
records = PLPlayersCrawler().run_sync() 
team_ids = set(str(r.get('team_source_id','')) for r in records) 
print('team_ids:', sorted(team_ids)[:10]) 
print('sample:', records[0]) 
