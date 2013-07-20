from flask import Flask, render_template, flash, redirect, request
from flask.ext.cache import Cache
from flask.ext.bootstrap import Bootstrap
from mongokit import Connection, Document
import steam
import pprint
import datetime

app = Flask(__name__)
app.config.from_pyfile("settings.cfg")
connection = Connection(app.config['MONGODB_HOST'],
                app.config['MONGODB_PORT'])

Bootstrap(app)
cache = Cache(app)
steam.api.key.set(app.config['STEAM_API_KEY'])
steam.api.socket_timeout.set(10)
schema = steam.items.schema(570, "en_US")

@connection.register
class Job(Document):
    __collection__ = 'jobs'
    __database__ = 'webdota'

    structure = {
        "account_id": int
    }

    required_fields = ['account_id']

    def __repr__(self):
        return "<Job {!r}>".format(self.account_id)

@app.template_filter('datetime')
def format_datetime(value):
    format = '%b %d, %Y %H:%M'
    return datetime.datetime.fromtimestamp(int(value)).strftime(format)

@cache.cached(timeout=60*60, key_prefix="league_passes")
def get_league_passes():
    return [x for x in schema if x.type == "League Pass"]

@connection.register
class Profile(Document):
    __collection__ = 'profiles'
    __database__ = 'webdota'

    structure = {
        "data": {},
        "account_id": int,
        "_last_updated": int
    }
    use_dot_notation = True

    def __repr__(self):
        return "<Profile {!r}>".format(self.account_id)

@app.route('/')
def index():
    return render_template("index.html", jobs=connection.Job.find(), profiles=connection.Profile.find())

@app.route('/search', methods=["GET"])
def search():
    account_id = request.args.get("account_id")
    if unicode.isdecimal(account_id):
        return redirect("/profile/{}".format(account_id))
    else:
        flash("Profile not found")
        return redirect("/")

@app.route("/profile/<int:account_id>")
def profile(account_id):
    data = connection.Profile.find_one({"account_id": account_id})
    if data is None:
        return redirect("/update/{}".format(account_id))
    else:
        owned_league_passes = [x["itemDef"] for x in data.data.leaguePasses or []]
        all_league_passes = get_league_passes()
        for x in all_league_passes :
            x.owned = True if x.schema_id in owned_league_passes else False
        return render_template("profile.html", profile=data, league_passes=all_league_passes, prettyprofile=pprint.pformat(data.data, indent=4))


@app.route("/update/<int:account_id>")
def update_profile_info(account_id):
    job = connection.Job.find_one({"account_id": account_id}) or connection.Job()
    job["account_id"] = account_id
    job.save()
    flash("Profile not in database, added to job queue.")
    return redirect("/")


if __name__ == '__main__':
    app.run()
