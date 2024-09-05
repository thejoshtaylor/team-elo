# Team Elo
# Josh Taylor - 2024

import os
import signal
import sqlite3
from itertools import permutations, combinations

# Defaults
START_ELO = 1000
MIN_TEAM = 3
MAX_TEAM = 13

# SQLite3 database
conn = None


# Create the database if it doesn't exist
def create_db():
    global conn
    if conn is None:
        conn = sqlite3.connect("players.db")
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS players (id INTEGER PRIMARY KEY, name TEXT, elo INT)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS synergy (sid INTEGER PRIMARY KEY, synergy INT)"
    )
    conn.commit()


# Close the database
def close_db():
    global conn
    if conn is not None:
        conn.close()


# Read in the database
def get_data():
    global conn
    create_db()
    c = conn.cursor()
    c.execute("SELECT * FROM players")
    players = c.fetchall()
    # get column names
    columns = [description[0] for description in c.description]
    # convert to dictionary
    players = [{col: player[i] for i, col in enumerate(columns)} for player in players]
    return players


# Write the data to the database
def write_data(players):
    global conn
    c = conn.cursor()
    c.execute("DELETE FROM players")
    c.executemany(
        "INSERT INTO players VALUES (NULL, ?, ?)",
        [(player["name"], player["elo"]) for player in players],
    )
    conn.commit()


# Get all synergy data from the database
def get_synergy_data():
    global conn
    create_db()
    c = conn.cursor()
    c.execute("SELECT * FROM synergy")
    synergy = c.fetchall()
    # get column names
    columns = [description[0] for description in c.description]
    # convert to dictionary
    synergy = [{col: syn[i] for i, col in enumerate(columns)} for syn in synergy]
    return synergy


# Get synergyID
def get_synergy_id(player1, player2):
    player1, player2 = sorted([player1, player2])
    return int(f"{player1:04d}{player2:04d}")


# Get players from synergyID
def get_players_from_synergy_id(synergy_id):
    return int(f"{synergy_id:08d}"[:4]), int(f"{synergy_id:08d}"[4:])


# Get synergy from database
def get_synergy(player1, player2):
    global conn
    synergyID = get_synergy_id(player1, player2)
    create_db()
    c = conn.cursor()
    c.execute("SELECT synergy FROM synergy WHERE sid = ?", (synergyID,))
    synergy = c.fetchone()
    if synergy is None:
        return 0
    return synergy[0]


# Get synergy from array
def get_synergy_from_data(synergy_data, player1, player2):
    synergyID = get_synergy_id(player1, player2)
    for s in synergy_data:
        if s["sid"] == synergyID:
            return s["synergy"]
    return 0


# Write synergy to database
def write_synergy_data(player1, player2, synergy):
    global conn
    c = conn.cursor()
    c.execute("UPSERT INTO synergy VALUES (?, ?)", (get_synergy_id(player1, player2), synergy))
    conn.commit()


# Print the title
def title():
    print()
    print(
        r"""
$$$$$$$$\                                      $$$$$$$$\ $$\           
\__$$  __|                                     $$  _____|$$ |          
   $$ | $$$$$$\   $$$$$$\  $$$$$$\$$$$\        $$ |      $$ | $$$$$$\  
   $$ |$$  __$$\  \____$$\ $$  _$$  _$$\       $$$$$\    $$ |$$  __$$\ 
   $$ |$$$$$$$$ | $$$$$$$ |$$ / $$ / $$ |      $$  __|   $$ |$$ /  $$ |
   $$ |$$   ____|$$  __$$ |$$ | $$ | $$ |      $$ |      $$ |$$ |  $$ |
   $$ |\$$$$$$$\ \$$$$$$$ |$$ | $$ | $$ |      $$$$$$$$\ $$ |\$$$$$$  |
   \__| \_______| \_______|\__| \__| \__|      \________|\__| \______/ 
                                                                       
"""
    )
    print("Josh Taylor - 2024")
    print()


def menu():
    print("[v] View Players")
    print("[n] New Player")
    print("[r] Remove Player")
    print("[u] Update Player")
    print("[g] Generate Teams")
    print("[q] Quit")
    print()

    res = input("> ").lower()
    while res not in ["v", "n", "r", "u", "g", "q"]:
        print("Invalid choice")
        res = input("> ").lower()

    return res


# Generate the team sizes
def generateTeamSizes(playerCount, MIN_SIZE=MIN_TEAM, MAX_SIZE=MAX_TEAM):
    # TODO allow for a team size that doesn't match, but where there's plentiful players
    options = []

    for i in range(MIN_SIZE, MAX_SIZE + 1):
        numTeams = playerCount // i
        if numTeams * i == playerCount:
            if numTeams % 2 == 0:
                options.append([(i, i)] * (numTeams // 2))

    return options


def generateCombos(playerIndexes, team_sizes=[5, 5]):
    if team_sizes == []:
        return []

    firstMember = None
    for combo in combinations(playerIndexes, team_sizes[0]):
        if firstMember is None:
            firstMember = combo[0]

        if len(team_sizes) == 1:
            yield [combo]
        else:
            # Make sure the first member is always in the set
            if firstMember not in combo:
                continue
            remaining = [p for p in playerIndexes if p not in combo]
            for subcombo in generateCombos(remaining, team_sizes[1:]):
                yield [combo] + subcombo


# Generate the team options
def generateOptions(players, team_sizes=[(5, 5)]):
    options = []

    # flatten team sizes
    flat_teams = [team for teams in team_sizes for team in teams]

    # generate all possible team combinations then package them in a dictionary
    combos = generateCombos(list(range(len(players))), flat_teams)
    synergy_data = get_synergy_data()
    for combo in combos:
        teams_dict = []
        for i, team in enumerate(combo):
            entry = {
                "team_number": i + 1,
                "players": [players[player] for player in team],
                "elo": sum([players[player]["elo"] for player in team])
                + get_team_synergy(synergy_data, [players[player] for player in team]),
            }
            teams_dict.append(entry)
        options.append(teams_dict)

    return options


def getUniquenessOfTeams(team1, team2):
    return len(set([player["name"] for player in team1 + team2])) - len(team1)


def getUniquenessOfOptions(option1, option2):
    # get lists of teams
    teams1 = [team["players"] for team in option1]
    teams2 = [team["players"] for team in option2]

    if len(teams1) != len(teams2):
        return len(teams1) + len(teams2)

    # generate all combinations of comparisons
    teams = list(range(1, len(teams1) + 1))
    uniquenesses = []
    for p in permutations(teams):
        uniqueness = 0
        for i in range(len(teams)):
            uniqueness += getUniquenessOfTeams(teams1[i], teams2[p[i] - 1])
        uniquenesses.append(uniqueness)

    return min(uniquenesses)


# Get the synergy amongst a team
def get_team_synergy(synergy_data, team):
    synergy = 0
    for i in range(len(team)):
        for j in range(i + 1, len(team)):
            synergy += get_synergy_from_data(synergy_data, team[i]["id"], team[j]["id"])
    return synergy


# Main function
def main():
    title()
    players = get_data()
    print(f"Read in {len(players)} players")
    print()

    while True:
        choice = menu()
        if choice == "v":
            print()
            for player in players:
                print(f"{player['name']} ({player['elo']})")
            print()
        elif choice == "n":
            name = input("Name: ")
            players.append({"name": name, "elo": START_ELO})
            print(f"Added {name} with an ELO of {START_ELO}")
            print()
            write_data(players)
        elif choice == "r":
            name = input("Name: ")
            for player in players:
                if player["name"] == name:
                    players.remove(player)
                    print(f"Removed {name}")
                    break
            print()
            write_data(players)
        elif choice == "u":
            name = input("Name: ")
            for player in players:
                if player["name"] == name:
                    new_elo = int(input("New ELO: "))
                    player["elo"] = new_elo
                    print(f"Updated {name} to {new_elo}")
                    break
            print()
            write_data(players)
        elif choice == "g":
            print()

            options = []

            for i, team_sizes in enumerate(generateTeamSizes(len(players))):
                options.extend(generateOptions(players, team_sizes))
            print()
            print(f"Generated {len(options)} options")
            print()

            # write options to file (just the names)
            # with open('options.csv', 'w') as f:
            #     writer = csv.writer(f, lineterminator='\n')
            #     for option in options:
            #         writer.writerow(sorted(','.join(sorted(player['name'] for player in team['players'])) for team in option))

            options.sort(
                key=lambda x: sum(
                    [abs(x[i]["elo"] - x[i + 1]["elo"]) for i in range(0, len(x), 2)]
                )
            )

            currentOption = options[0]
            # print elo differences
            for j, option in enumerate(options):
                x = 0
                print(f"[{j+1:3d}]", end=" ")
                for i in range(0, len(option), 2):
                    print(f"({option[i]['elo']} - {option[i + 1]['elo']})", end=" + ")
                    x += abs(option[i]["elo"] - option[i + 1]["elo"])
                print(f"\b\b= {x}", end="")
                print(f" ({getUniquenessOfOptions(currentOption, option)})")
                if j >= 9:
                    break

            print()
        elif choice == "q":
            break


# Signal handler
def signal_handler(sig, frame):
    close_db()
    print("SIGNAL RECEIVED: Exiting")
    os._exit(0)


# trigger signal handler on interrupt
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    main()
    close_db()
