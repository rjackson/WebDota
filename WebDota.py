from flask import Flask, render_template, flash, redirect, request
from flask.ext.cache import Cache
from flask.ext.bootstrap import Bootstrap
from mongokit import Connection
import steam
import pprint

from models import Profile, Job, Match
from filters import unix_strftime
app = Flask(__name__)
app.config.from_pyfile("settings.cfg")
connection = Connection(app.config['MONGODB_HOST'],
                        app.config['MONGODB_PORT'])

Bootstrap(app)
cache = Cache(app)
connection.register([Profile, Job, Match])
app.add_template_filter(unix_strftime)

# Setup steamodd
steam.api.key.set(app.config['STEAM_API_KEY'])
steam.api.socket_timeout.set(10)
schema = steam.items.schema(570, "en_US")


@cache.cached(timeout=60*60, key_prefix="league_passes")
def get_league_passes():
    return [x for x in schema if x.type == "League Pass"]


@cache.cached(timeout=60*60, key_prefix="heroes")
def get_heroes():
    res = steam.api.interface("IEconDOTA2_570").GetHeroes(language="en_US").get("result")
    return {x["id"]: x["localized_name"] for x in res.get("heroes")}


@app.template_filter("get_hero_name")
def get_hero_name(hero_id):
    try:
        return [get_heroes().get(x) for x in hero_id]
    except TypeError:
        return get_heroes().get(hero_id)

@app.route('/')
def index():
    return render_template("index.html",
                           jobs=connection.Job.find(),
                           profiles=connection.Profile.find(),
                           matches=connection.Match.find(),
                           title="WebDota - An experiment in getting banned.")


@app.route("/profile/<int:_id>")
def profile(_id):
    data = connection.Profile.find_one({"id": _id})
    if data is None:
        return update(_type="account", _id=_id)
    else:
        owned_league_passes = [x["itemDef"] for x in data.data.leaguePasses or []]
        all_league_passes = get_league_passes()
        for x in all_league_passes :
            x.owned = True if x.schema_id in owned_league_passes else False

        commendations = {
            "friendly": int(data.data.gameAccountClient.friendly),
            "forgiving": int(data.data.gameAccountClient.forgiving),
            "teaching": int(data.data.gameAccountClient.teaching),
            "leadership": int(data.data.gameAccountClient.leadership)
        }
        commendations["total"] = sum(commendations.values()) or 1
        commendations["friendly_pc"] = (float(commendations["friendly"]) / commendations["total"]) * 100.0 or 25
        commendations["forgiving_pc"] = (float(commendations["forgiving"]) / commendations["total"]) * 100.0 or 25
        commendations["teaching_pc"] = (float(commendations["teaching"]) / commendations["total"]) * 100.0 or 25
        commendations["leadership_pc"] = (float(commendations["leadership"]) / commendations["total"]) * 100.0 or 25

        matches = connection.Match.find({"data.match.players": {"$elemMatch": {"accountId": data.id}}})

        return render_template("profile.html",
                               profile=data,
                               commendations=commendations,
                               league_passes=all_league_passes,
                               matches=matches,
                               prettydata=pprint.pformat(data.data, indent=4),
                               title=data.data.playerName)


@app.route("/match/<int:_id>")
def match(_id):
    data = connection.Match.find_one({"id": _id})
    if data is None:
        return update(_type="match", _id=_id)
    else:
        return render_template("match.html",
                               match=data,
                               prettydata=pprint.pformat(data.data, indent=4),
                               title="Match {}".format(data.id))


@app.route('/search', methods=["GET"])
def search():
    # Default type to 'account'.
    _type, _id = request.args.get("type", "account"), request.args.get("id")

    if not _id:
        flash("You must provide an ID with your search.", "error")
        return redirect("/")
    if _type == "account":
        if unicode.isdecimal(unicode(_id)):
            return redirect("/profile/{}".format(_id))
        else:
            flash("Profile ID must be decimal!", "error")
            return redirect("/")
    elif _type == "match":
        if unicode.isdecimal(unicode(_id)):
            return redirect("/match/{}".format(_id))
        else:
            flash("Match ID must be decimal!", "error")
            return redirect("/")
    else:
        flash("Search type not recognized! The authorities have been notified.", "error")
        print("Bad search type.  Search parameters: {}".format(request.args))
        return redirect("/")


@app.route("/update")
def update(_type=None, _id=None):
    _type = _type or request.args.get("type")
    _id = _id or request.args.get("id")

    if not _id:
        flash("You must provide an ID with your update request.", "error")
        return redirect("/")

    if not _type:
        flash("You must provide a type with your update request.", "error")
        return redirect("/")

    if _type == "account":
        if unicode.isdecimal(unicode(_id)):
            _id = int(_id)
        else:
            flash("Profile ID must be decimal!", "error")
            return redirect("/")
    elif _type == "match":
        if unicode.isdecimal(unicode(_id)):
            _id = int(_id)
        else:
            flash("Match ID must be decimal!", "error")
            return redirect("/")
    else:
        flash("Update type not recognized! The authorities have been notified.", "error")
        print("Bad update type.  Search parameters: {}".format(request.args))
        return redirect("/")

    job = connection.Job.find_one({"type": _type, "id": _id}) or connection.Job()
    job["type"], job["id"] = _type, _id
    job.save()

    flash("Update job, {}, added to job queue.".format((_type, _id)), "info")
    return redirect("/")

# noinspection PyUnusedLocal
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', title="404 - Nobody likes you."), 404

if __name__ == '__main__':
    app.run()
