import os
import tempfile
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
import urllib
import base64

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

        liste = df2.groupby(["fullName"]).first().sort_values('playerName',ascending=False)

        isimler = liste['playerName']
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

                if playerId == "":
                        flash('Select a player!')
                        return redirect("/")  
                
                else:
                        playerId = int(playerId)
                        df = pd.read_csv("https://raw.githubusercontent.com/kovacs5/fotmob_csv/main/stsl_final.csv")
                        df = df[df["playerId"] == playerId]
                        df_npxg = df[df["situation"] != "Penalty"]
                        df_isabetli = df[df["expectedGoalsOnTarget"].notnull()]

                        teamId_1 = df["teamId"]
                        teamId = teamId_1.iloc[-1]
                        playerName_1 = df["playerName"]
                        playerName = playerName_1.iloc[-1]

                        IMAGE_URL = 'https://images.fotmob.com/image_resources/playerimages/' + str(playerId) + '.png'
                        player_logo = Image.open(urlopen(IMAGE_URL))

                        IMAGE_URL1 = 'https://images.fotmob.com/image_resources/logo/teamlogo/' + str(teamId) + '.png'
                        team_logo = Image.open(urlopen(IMAGE_URL1))

                        goal = df[df["eventType"] == "Goal"].copy()
                        miss = df[(df["eventType"] == "Miss") | (df["eventType"] == "Post")].copy()
                        blocked = df[df["eventType"] == "AttemptSaved"].copy()
                        on_target = len(df[(df["isOnTarget"] == True) & (df["isBlocked"] == False)].copy())
                        off_target = len(df[df["isOnTarget"] == False].copy())

                        tot_shots = df.shape[0]
                        tot_goals = goal.shape[0]
                        tot_xg = df["expectedGoals"].sum().round(2)
                        tot_xgot = df["expectedGoalsOnTarget"].sum().round(2)
                        tot_npxg = df_npxg["expectedGoals"].sum().round(2)

                        pitch = VerticalPitch(half=True, pitch_type='uefa', pitch_color='#1D1D1D', line_color='#818f86', goal_type='box')

                        fig, ax = pitch.draw(figsize=(10, 8))
                        fig.patch.set_facecolor('#1D1D1D')
                        fig.set_figwidth(7.5)

                        sc_goal = pitch.scatter(goal["x"], goal["y"],
                                        s=goal["expectedGoalsOnTarget"]*800,
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

                        ligsayisi = pd.unique(df['league_name'])
                        lig1 = str(pd.unique(df['league_name'])[0])
                        sezon = str(pd.unique(df['league_season'])[0])
                        sezon1 = sezon[2:5]
                        sezon2 = sezon[7:]
                        sezon_adi = sezon1+sezon2

                        if len(ligsayisi) == 1:
                                TITLE_STR2 = lig1 + " | " + sezon_adi

                        if len(ligsayisi) > 1:
                                lig2 = str(pd.unique(df['league_name'])[1])
                                TITLE_STR2 = lig1 + " & " + lig2 + " | " + sezon_adi

                        TITLE_STR3 = '@bariscanyeksin'

                        title1_text = fig.text(0.5, 0.94, TITLE_STR1, fontsize=17.5, color='white',
                                                        ha='center', va='center', fontproperties=prop_bold)

                        title2_text = fig.text(0.5, 0.9035, TITLE_STR2, fontsize=13, color='white',
                                                        ha='center', va='center', fontproperties=prop)

                        title3_text = fig.text(0.5, 0.866, TITLE_STR3, fontsize=10, color='white',
                                                        ha='center', va='center', fontproperties=prop)

                        back_box = dict(boxstyle='round', facecolor='wheat', alpha=0.9)
                        back_box_2 = dict(boxstyle='round, pad=0.4', facecolor='#facd5c', alpha=0.9)

                        ax.text(38, 75.5, "Goals", size=9, ha="center", fontproperties=prop, bbox=back_box, color='black')
                        ax.text(38, 72, "Shots", size=9, ha="center", fontproperties=prop, bbox=back_box, color='black')
                        ax.text(38, 68.5, "On Target", size=9, ha="center", fontproperties=prop, bbox=back_box, color='black')
                        ax.text(38, 65, "Off Target", size=9, ha="center", fontproperties=prop, bbox=back_box, color='black')
                        ax.text(38, 61.5, "xG", size=9, ha="center", fontproperties=prop, bbox=back_box, color='black')
                        ax.text(38, 58, "npxG", size=9, ha="center", fontproperties=prop, bbox=back_box, color='black')
                        ax.text(38, 54.5, "xGOT", size=9, ha="center", fontproperties=prop, bbox=back_box, color='black')

                        ax.text(30, 75.5, str(tot_goals), size=9, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                        ax.text(30, 72, str(tot_shots), size=9, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                        ax.text(30, 68.5, str(on_target), size=9, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                        ax.text(30, 65, str(off_target), size=9, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                        ax.text(30, 61.5, str(tot_xg), size=9, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                        ax.text(30, 58, str(tot_npxg), size=9, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
                        ax.text(30, 54.5, str(tot_xgot), size=9, ha="center", fontproperties=prop, bbox=back_box_2, color='black')

                        fig.text(0.09225, 0.2125, "-  xG  +", size=8, ha="left", fontfamily='Poppins', color='white')

                        fig.text(0.90775, 0.2125, "Data: FotMob", size=8, ha="right", fontfamily='Poppins', color='white')

                        canvas = FigureCanvas(fig)
                        output = io.BytesIO()
                        canvas.print_png(output)
                        response = make_response(output.getvalue())
                        response.mimetype = 'image/png'
                        return response

if __name__ == '__main__':
    app.run()