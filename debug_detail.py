"""
DEBUG: scripts/debug_ucl_stats.py
Kiểm tra xem UCL crawler trả đúng và đủ stats chưa
"""
import json
import logging
from typing import Dict, List
from scripts.crawlers.ucl_players import UCLPlayersCrawler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


# Color codes for terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(title):
    """Print fancy header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}\n")


def print_section(title):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}▶ {title}{Colors.RESET}")
    print(f"{Colors.YELLOW}{'-' * 80}{Colors.RESET}")


def print_ok(msg):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def print_error(msg):
    """Print error message"""
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")


def print_warning(msg):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")


def print_info(msg):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")


class UCLStatsDebugger:
    """Debug UCL player stats"""

    REQUIRED_STATS = {
        'goals', 'assists', 'yellow_cards', 'red_cards',
        'appearances', 'minutes_played', 'saves', 'clean_sheets',
        'average_rating', 'expected_goals'
    }

    REQUIRED_INFO = {
        'source_id', 'name', 'league', 'season', 'position',
        'team_source_id', 'team_name', 'nationality', 'photo_url'
    }

    def __init__(self):
        self.crawler = UCLPlayersCrawler()
        self.players = []
        self.issues = []
        self.stats = {}

    def fetch_and_parse(self):
        """Fetch dữ liệu từ API và parse"""
        print_section("STEP 1: Fetch Data từ FotMob API")

        try:
            print_info("Fetching data từ FotMob...")
            data = self.crawler.fetch()

            if not data:
                print_error("Không lấy được data từ API!")
                return False

            print_ok(f"Fetched data thành công")
            print_info(f"Data keys: {list(data.keys())}")

            # Check overview
            overview = data.get('overview', {})
            print_info(f"Overview keys: {list(overview.keys())}")

            # Check fixtures
            fixtures = data.get('fixtures', {})
            all_matches = fixtures.get('allMatches', [])
            print_info(f"Fixtures có {len(all_matches)} matches")

            print_ok("Data structure OK")

        except Exception as e:
            print_error(f"Error fetching data: {e}")
            return False

        # Parse dữ liệu
        print_section("STEP 2: Parse Data")

        try:
            print_info("Parsing players...")
            self.players = self.crawler.parse(data)
            print_ok(f"Parsed {len(self.players)} players")

        except Exception as e:
            print_error(f"Error parsing data: {e}")
            import traceback
            traceback.print_exc()
            return False

        return True

    def check_player_count(self):
        """Kiểm tra số lượng players"""
        print_section("STEP 3: Player Count Analysis")

        total = len(self.players)
        with_goals = sum(1 for p in self.players if p.get('goals', 0) > 0)
        with_assists = sum(1 for p in self.players if p.get('assists', 0) > 0)
        with_yellow = sum(1 for p in self.players if p.get('yellow_cards', 0) > 0)
        gk_count = sum(1 for p in self.players if p.get('position') == 'GK')

        print_info(f"Total players: {total}")
        print_info(f"Players with goals > 0: {with_goals}")
        print_info(f"Players with assists > 0: {with_assists}")
        print_info(f"Players with yellow_cards > 0: {with_yellow}")
        print_info(f"GK count: {gk_count}")

        # Expected values
        if with_goals >= 280:
            print_ok(f"✓ Goals count OK ({with_goals} >= 280)")
        else:
            print_error(f"✗ Goals count LOW ({with_goals} < 280)")
            self.issues.append(f"Goals count too low: {with_goals}")

        if with_assists >= 100:
            print_ok(f"✓ Assists count OK ({with_assists} >= 100)")
        else:
            print_warning(f"⚠ Assists count might be low ({with_assists})")

        if gk_count >= 20:
            print_ok(f"✓ GK count OK ({gk_count})")
        else:
            print_warning(f"⚠ GK count might be low ({gk_count})")

        self.stats['total'] = total
        self.stats['with_goals'] = with_goals
        self.stats['with_assists'] = with_assists
        self.stats['with_yellow'] = with_yellow
        self.stats['gk_count'] = gk_count

    def check_data_completeness(self):
        """Kiểm tra dữ liệu có đủ không"""
        print_section("STEP 4: Data Completeness Check")

        missing_fields = {field: 0 for field in self.REQUIRED_STATS | self.REQUIRED_INFO}
        players_with_zero_stats = []

        for player in self.players:
            # Check required info
            for field in self.REQUIRED_INFO:
                if field not in player or not player.get(field):
                    missing_fields[field] += 1

            # Check if player has all zero stats (ghost player)
            stats_values = [player.get(s, 0) for s in self.REQUIRED_STATS]
            if all(v == 0 for v in stats_values):
                players_with_zero_stats.append({
                    'id': player.get('source_id'),
                    'name': player.get('name'),
                    'position': player.get('position')
                })

        # Report missing fields
        print_info("Missing fields count:")
        for field, count in missing_fields.items():
            if count > 0:
                if count <= 10:
                    print_warning(f"  {field}: {count} missing")
                else:
                    print_error(f"  {field}: {count} missing")
            else:
                print_ok(f"  {field}: ✓")

        # Report zero-stat players
        if players_with_zero_stats:
            print_warning(f"Found {len(players_with_zero_stats)} players with ALL zero stats:")
            for p in players_with_zero_stats[:10]:
                print(f"    - {p['name']} ({p['position']}) [ID: {p['id']}]")
            if len(players_with_zero_stats) > 10:
                print(f"    ... and {len(players_with_zero_stats) - 10} more")
        else:
            print_ok("No players with all-zero stats")

        self.stats['players_with_zero_stats'] = len(players_with_zero_stats)

    def check_top_scorers(self):
        """Kiểm tra top scorers (phải khớp với FotMob)"""
        print_section("STEP 5: Top Scorers Analysis")

        # Sort by goals
        sorted_players = sorted(self.players, key=lambda p: p.get('goals', 0), reverse=True)

        print_info("Top 10 scorers:")
        print(f"{Colors.BOLD}{'Rank':<5} {'Name':<25} {'Team':<20} {'Goals':<8} {'Apps':<6}{Colors.RESET}")
        print("-" * 80)

        for i, p in enumerate(sorted_players[:10], 1):
            name = p.get('name', 'Unknown')[:24]
            team = p.get('team_name', 'Unknown')[:19]
            goals = p.get('goals', 0)
            apps = p.get('appearances', 0)

            # Expected top scorers
            expected_top = {
                'Mbappé': 14,
                'Kane': 11,
                'Dani Olmo': 8,
                'Lewandowski': 8,
            }

            # Check if this is expected
            is_expected = any(exp in name for exp in expected_top.keys())
            marker = f"{Colors.GREEN}✓{Colors.RESET}" if is_expected else " "

            print(f"{i:<5} {name:<25} {team:<20} {goals:<8} {apps:<6} {marker}")

        # Verify known top scorers
        print_info("\nVerifying known top scorers:")
        mbappe = next((p for p in self.players if 'Mbappé' in p.get('name', '')), None)
        kane = next((p for p in self.players if 'Kane' in p.get('name', '')), None)

        if mbappe:
            if mbappe.get('goals') == 14:
                print_ok(f"✓ Mbappé: {mbappe['goals']} goals (CORRECT)")
            else:
                print_error(f"✗ Mbappé: {mbappe['goals']} goals (Expected 14)")
                self.issues.append(f"Mbappé goals wrong: {mbappe['goals']} vs 14")
        else:
            print_warning("⚠ Mbappé not found")

        if kane:
            if kane.get('goals') == 11:
                print_ok(f"✓ Kane: {kane['goals']} goals (CORRECT)")
            else:
                print_error(f"✗ Kane: {kane['goals']} goals (Expected 11)")
                self.issues.append(f"Kane goals wrong: {kane['goals']} vs 11")
        else:
            print_warning("⚠ Kane not found")

    def check_stats_distribution(self):
        """Kiểm tra phân bố stats"""
        print_section("STEP 6: Stats Distribution Analysis")

        goals_dist = {
            '0': 0, '1-2': 0, '3-5': 0, '6-10': 0, '11-14': 0, '15+': 0
        }

        assists_dist = {
            '0': 0, '1-2': 0, '3-5': 0, '6+': 0
        }

        yellow_dist = {
            '0': 0, '1-2': 0, '3+': 0
        }

        for p in self.players:
            goals = p.get('goals', 0)
            assists = p.get('assists', 0)
            yellow = p.get('yellow_cards', 0)

            # Goals distribution
            if goals == 0:
                goals_dist['0'] += 1
            elif goals <= 2:
                goals_dist['1-2'] += 1
            elif goals <= 5:
                goals_dist['3-5'] += 1
            elif goals <= 10:
                goals_dist['6-10'] += 1
            elif goals <= 14:
                goals_dist['11-14'] += 1
            else:
                goals_dist['15+'] += 1

            # Assists distribution
            if assists == 0:
                assists_dist['0'] += 1
            elif assists <= 2:
                assists_dist['1-2'] += 1
            elif assists <= 5:
                assists_dist['3-5'] += 1
            else:
                assists_dist['6+'] += 1

            # Yellow cards distribution
            if yellow == 0:
                yellow_dist['0'] += 1
            elif yellow <= 2:
                yellow_dist['1-2'] += 1
            else:
                yellow_dist['3+'] += 1

        print_info("Goals distribution:")
        for key in ['0', '1-2', '3-5', '6-10', '11-14', '15+']:
            print(f"  {key:<8}: {goals_dist[key]:>4} players")

        print_info("\nAssists distribution:")
        for key in ['0', '1-2', '3-5', '6+']:
            print(f"  {key:<8}: {assists_dist[key]:>4} players")

        print_info("\nYellow cards distribution:")
        for key in ['0', '1-2', '3+']:
            print(f"  {key:<8}: {yellow_dist[key]:>4} players")

    def save_debug_json(self):
        """Save chi tiết players to JSON"""
        print_section("STEP 7: Saving Debug JSON")

        output_file = 'debug_ucl_players.json'

        try:
            # Save top 20 scorers
            sorted_players = sorted(self.players, key=lambda p: p.get('goals', 0), reverse=True)
            top_20 = sorted_players[:20]

            debug_data = {
                'total_count': len(self.players),
                'with_goals_count': self.stats.get('with_goals', 0),
                'stats_summary': self.stats,
                'top_20_scorers': top_20
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, indent=2, ensure_ascii=False)

            print_ok(f"Saved to {output_file}")
            print_info(f"File size: {len(json.dumps(debug_data)) / 1024:.1f} KB")

        except Exception as e:
            print_error(f"Error saving JSON: {e}")

    def save_full_debug_json(self):
        """Save tất cả players to JSON"""
        output_file = 'debug_ucl_players_full.json'

        try:
            debug_data = {
                'total_count': len(self.players),
                'with_goals_count': self.stats.get('with_goals', 0),
                'stats_summary': self.stats,
                'all_players': self.players
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, indent=2, ensure_ascii=False)

            print_ok(f"Saved all players to {output_file}")
            print_info(f"File size: {len(json.dumps(debug_data)) / 1024 / 1024:.1f} MB")

        except Exception as e:
            print_error(f"Error saving full JSON: {e}")

    def print_summary(self):
        """Print final summary"""
        print_header("FINAL SUMMARY")

        print(f"{Colors.BOLD}Overall Status:{Colors.RESET}")
        print(f"  Total Players: {self.stats.get('total', 0)}")
        print(f"  With Goals > 0: {self.stats.get('with_goals', 0)}")
        print(f"  With Assists > 0: {self.stats.get('with_assists', 0)}")
        print(f"  With Yellow Cards > 0: {self.stats.get('with_yellow', 0)}")
        print(f"  GK Count: {self.stats.get('gk_count', 0)}")
        print(f"  Players with all-zero stats: {self.stats.get('players_with_zero_stats', 0)}")

        if self.issues:
            print(f"\n{Colors.RED}{Colors.BOLD}Issues Found:{Colors.RESET}")
            for issue in self.issues:
                print(f"  {Colors.RED}✗ {issue}{Colors.RESET}")
        else:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ No Critical Issues Found{Colors.RESET}")

        print(f"\n{Colors.BOLD}Next Steps:{Colors.RESET}")
        print(f"  1. Check JSON files:")
        print(f"     - debug_ucl_players.json (top 20 scorers)")
        print(f"     - debug_ucl_players_full.json (all players)")
        print(f"  2. Verify stats match FotMob website")
        print(f"  3. If OK → Run: python scripts/run_all.py --only players")
        print(f"  4. Then verify in database")


def main():
    """Main debug function"""
    print_header("UCL PLAYER STATS DEBUG")

    print_info("This script will:")
    print_info("  1. Fetch data from FotMob API")
    print_info("  2. Parse UCL player data")
    print_info("  3. Analyze stats completeness")
    print_info("  4. Check top scorers")
    print_info("  5. Generate debug JSON files")

    debugger = UCLStatsDebugger()

    # Run all checks
    if not debugger.fetch_and_parse():
        print_error("Failed to fetch/parse data!")
        return

    debugger.check_player_count()
    debugger.check_data_completeness()
    debugger.check_top_scorers()
    debugger.check_stats_distribution()
    debugger.save_debug_json()
    debugger.save_full_debug_json()

    debugger.print_summary()


if __name__ == "__main__":
    main()