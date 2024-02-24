import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.font_manager as fm
from mplsoccer import VerticalPitch, add_image
from PIL import Image
from urllib.request import urlopen
import pandas as pd
from flask import Flask, render_template, request, flash, make_response, redirect, Response
import io
import json
from bs4 import BeautifulSoup
import requests

import json

matplotlib.rcParams["figure.dpi"] = 300

fpath = "fonts/Poppins/Poppins-Regular.ttf"
prop = fm.FontProperties(fname=fpath)

fpath_bold = "fonts/Poppins/Poppins-SemiBold.ttf"
prop_bold = fm.FontProperties(fname=fpath_bold)

fpath_bold2 = "fonts/Poppins/Poppins-Bold.ttf"
prop_bold2 = fm.FontProperties(fname=fpath_bold2)

app = Flask(__name__)
app.secret_key = "FotMob_Shotmap"

@app.route("/", methods=['GET', 'POST'])
def index():  
        df2 = pd.read_csv("https://raw.githubusercontent.com/kovacs5/fotmob_csv/main/stsl_final.csv")
        df2.drop(['eventType'], axis=1)
        liste = df2.groupby(by=["fullName","playerId"], as_index=False).sum().sort_values('playerName',ascending=False)
        liste = liste[liste['expectedGoals'] >= 1].reset_index()

        isimler = liste['fullName']
        playerids = liste['playerId']

        merged_list = [(playerids[i], isimler[i]) for i in range(0, len(isimler))][::-1]

        choices = merged_list
        selected = request.args.get('choice','1')
        state = {'choice':selected}  

        return render_template('index.html', choices=choices, state=state)

@app.route("/plot.png", methods=['GET', 'POST'])
def result():
        if request.method == "POST":
               
                playerId = request.form.get('playerId_input')

                if ((playerId == "") | (playerId == "selectaplayer")):
                        flash('Player is not selected!')
                        return redirect("/")  
                
                else:
                        playerId = int(playerId)

                        stsl_final_csv = pd.read_csv("https://raw.githubusercontent.com/kovacs5/fotmob_csv/main/stsl_final.csv")
                        oyuncu_df = stsl_final_csv[stsl_final_csv['playerId'] == playerId]
                        teamId = oyuncu_df['teamId'].iloc[-1]

                        fotmob_player_info_url = "https://www.fotmob.com/api/playerData?id="+str(playerId)
                        response2 = urlopen(fotmob_player_info_url) 
                        player_info_json = json.loads(response2.read())
                        playerName = player_info_json["name"]
                        leagueId = 71
                        leagueName = "Süper Lig"
                        season_text = player_info_json["mainLeague"]["season"]
                        season_text = season_text.split("/")
                        season_1 = season_text[0][2:]
                        season_2 = season_text[1][2:]
                        season = season_1 + "/" + season_2

                        fotmob_player_url = "https://www.fotmob.com/api/playerStats?playerId="+str(playerId)+"&seasonId=2023/2024-"+str(leagueId)
                        response = urlopen(fotmob_player_url) 
                        data_json = json.loads(response.read())
                        data_json_shotmap = data_json["shotmap"]
                        fotmob_shotmap_df = pd.json_normalize(data_json_shotmap)

                        goal = fotmob_shotmap_df[fotmob_shotmap_df["eventType"] == "Goal"].copy()
                        miss = fotmob_shotmap_df[(fotmob_shotmap_df["eventType"] == "Miss") | (fotmob_shotmap_df["eventType"] == "Post")].copy()
                        blocked = fotmob_shotmap_df[fotmob_shotmap_df["eventType"] == "AttemptSaved"].copy()

                        minute_stats = data_json["topStatCard"]["items"]
                        minutes = minute_stats[5]["statValue"]

                        detailed_stats = data_json["statsSection"]["items"][0]["items"]
                        if len(detailed_stats) == 6:
                                tot_goals = detailed_stats[0]["statValue"]
                                tot_shots = detailed_stats[4]["statValue"]
                                on_target = detailed_stats[5]["statValue"]
                                tot_xg = detailed_stats[1]["statValue"]
                                tot_npxg = detailed_stats[3]["statValue"]
                                tot_xgot = detailed_stats[2]["statValue"]
                        
                        elif len(detailed_stats) != 6:
                                tot_goals = detailed_stats[0]["statValue"]
                                tot_shots = detailed_stats[5]["statValue"]
                                on_target = detailed_stats[6]["statValue"]
                                tot_xg = detailed_stats[1]["statValue"]
                                tot_npxg = detailed_stats[4]["statValue"]
                                tot_xgot = detailed_stats[2]["statValue"]

                        IMAGE_URL = 'https://images.fotmob.com/image_resources/playerimages/' + str(playerId) + '.png'
                        player_logo = Image.open(urlopen(IMAGE_URL))

                        IMAGE_URL1 = 'https://images.fotmob.com/image_resources/logo/teamlogo/' + str(teamId) + '.png'
                        team_logo = Image.open(urlopen(IMAGE_URL1))

                        pitch = VerticalPitch(half=True, pitch_type='uefa', pitch_color='#272727', line_color='#818f86', goal_type='box')

                        fig, ax = pitch.draw(figsize=(10, 8))
                        fig.patch.set_facecolor('#272727')
                        fig.set_figwidth(7.5)

                        sc_goal = pitch.scatter(goal["x"], goal["y"],
                                        s=goal["expectedGoals"]*700,
                                        c="#F2D61F", alpha=0.9,
                                        marker="*",
                                        ax=ax)

                        sc_miss = pitch.scatter(miss["x"], miss["y"],
                                        s=miss["expectedGoals"]*700,
                                        c="#E72B2C", alpha=0.9,
                                        marker="x",
                                        ax=ax,
                                        edgecolor="#101010")

                        sc_blocked = pitch.scatter(blocked["x"], blocked["y"],
                                        s=blocked["expectedGoals"]*700,
                                        c="#6496DD", alpha=0.9,
                                        marker="o",
                                        ax=ax,
                                        edgecolor="#101010")

                        pitch.scatter(57,62.9,
                                        s=150,
                                        c="#6496DD", alpha=0.9,
                                        marker="o",
                                        ax=ax,
                                        edgecolor="#101010")

                        pitch.scatter(57,64.7,
                                        s=75,
                                        c="#6496DD", alpha=0.9,
                                        marker="o",
                                        ax=ax,
                                        edgecolor="#101010")

                        pitch.scatter(57,66.035,
                                        s=25,
                                        c="#6496DD", alpha=0.9,
                                        marker="o",
                                        ax=ax,
                                        edgecolor="#101010")

                        goals_symbol = pitch.scatter(-100, -100,
                                        s=300,
                                        c="#F2D61F", alpha=0.9,
                                        marker="*",
                                        ax=ax,
                                        label="Goals")

                        blocked_symbol = pitch.scatter(-100, -100,
                                        s=225,
                                        c="#6496DD", alpha=0.9,
                                        marker="o",
                                        ax=ax,
                                        edgecolor="#101010",
                                        label="Saved/Blocked")

                        miss_symbol = pitch.scatter(-100, -100,
                                        s=150,
                                        c="#E72B2C", alpha=0.9,
                                        marker="x",
                                        ax=ax,
                                        edgecolor="#101010",
                                        label="Miss")

                        ax.legend(facecolor='None', edgecolor='None', labelcolor='white', fontsize=9, loc='lower center', ncol=3, 
                                alignment='center', columnspacing=2, labelspacing=1, handletextpad=0.4, bbox_to_anchor=(0.5, -0.15), prop=prop)

                        ax_image_1 = add_image(player_logo, fig, interpolation='hanning', left=0.123, bottom=0.85, width=0.12)

                        ax_image_2 = add_image(team_logo, fig, interpolation='hanning', left=0.753, bottom=0.85, width=0.12)

                        TITLE_STR1 = playerName + " Shots"
                        TITLE_STR2 = leagueName + " | " + season
                        TITLE_STR3 = '@bariscanyeksin'

                        title1_text = fig.text(0.5, 0.94, TITLE_STR1, fontsize=17.5, color='white',
                                                        ha='center', va='center', fontproperties=prop_bold)

                        title2_text = fig.text(0.5, 0.9035, TITLE_STR2, fontsize=13, color='white',
                                                        ha='center', va='center', fontproperties=prop)

                        title3_text = fig.text(0.5, 0.866, TITLE_STR3, fontsize=10, color='white',
                                                        ha='center', va='center', fontproperties=prop)

                        back_box = dict(boxstyle='round', facecolor='wheat', alpha=0.9)
                        back_box_2 = dict(boxstyle='round, pad=0.4', facecolor='#facd5c', alpha=0.9)
                        back_box_3 = dict(boxstyle='round, pad=0.4', facecolor='#ffffff', alpha=0.7)

                        ax.text(38, 72, "Goals", size=9, ha="center", fontproperties=prop, bbox=back_box, color='black')
                        ax.text(38, 68.5, "Shots", size=9, ha="center", fontproperties=prop, bbox=back_box, color='black')
                        ax.text(38, 65, "On Target", size=9, ha="center", fontproperties=prop, bbox=back_box, color='black')
                        ax.text(38, 61.5, "xG", size=9, ha="center", fontproperties=prop, bbox=back_box, color='black')
                        ax.text(38, 58, "npxG", size=9, ha="center", fontproperties=prop, bbox=back_box, color='black')
                        ax.text(38, 54.5, "xGOT", size=9, ha="center", fontproperties=prop, bbox=back_box, color='black')

                        ax.text(30, 72, str(tot_goals), size=9, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                        ax.text(30, 68.5, str(tot_shots), size=9, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                        ax.text(30, 65, str(on_target), size=9, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                        ax.text(30, 61.5, str(tot_xg), size=9, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                        ax.text(30, 58, str(tot_npxg), size=9, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                        ax.text(30, 54.5, str(tot_xgot), size=9, ha="center", fontproperties=prop, bbox=back_box_2, color='black')

                        ax.text(34, 49.5, str(minutes)+" min'", size=9, ha="center", fontproperties=prop, bbox=back_box_3, color='black')

                        fig.text(0.09225, 0.2125, "-  xG  +", size=8, ha="left", fontproperties=prop, color='white')

                        fig.text(0.90775, 0.2125, "Data: FotMob", size=8, ha="right", fontproperties=prop, color='white')

                        canvas = FigureCanvas(fig)
                        output = io.BytesIO()
                        canvas.print_png(output)
                        response = make_response(output.getvalue())
                        response.mimetype = 'image/png'
                        return response

if __name__ == '__main__':
    app.run()
