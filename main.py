from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
import requests
from forms import RateMovieForm, AddMovieForm

API_KEY = "Your API KEY goes here"
TMDB_BASE_URL = "https://api.themoviedb.org/3/"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///favourite_movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


# db.create_all()
#
# new_movie = Movie(
#     title="Phone Booth",
#     year="2002",
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# db.session.add(new_movie)
# db.session.commit()

def get_movie_info_for(movie_id):
    """
    Gets new record information from tmdb api and returns a Movie db object
    :param movie_id: int - the tmdb movie id
    :return: Movie db object
    """
    id_search_url = TMDB_BASE_URL + f"movie/{movie_id}"
    response = requests.get(id_search_url, params={"api_key": API_KEY})

    response.raise_for_status()
    movie = response.json()
    movie_to_add = Movie(
        title=movie['title'],
        year=int(movie['release_date'][:4]),
        description=movie['overview'],
        img_url=f"{TMDB_IMAGE_BASE_URL}{movie['poster_path']}",
    )

    return movie_to_add


def search_tmdb_for(title):
    """Returns a list of movies for a given title

    :param title: string - the desired movie title
    :return: [string] - a list of dictionaries titles and dates
    """
    title_search_url = TMDB_BASE_URL + "search/movie"
    response = requests.get(title_search_url, params={"api_key": API_KEY, "query": title})
    response.raise_for_status()
    movie_titles_and_dates = response.json()['results']

    return movie_titles_and_dates


@app.route("/add_record")
def add_record():
    tmdb_movie_id = request.args.get('id')

    movie_to_add = get_movie_info_for(tmdb_movie_id)
    db.session.add(movie_to_add)
    db.session.commit()

    movie = Movie.query.filter_by(title=movie_to_add.title).first()
    print(f"local movie id: {movie.id}")
    return redirect(url_for('update', id=movie.id))


@app.route("/add", methods=['GET', 'POST'])
def add_movie():
    form = AddMovieForm()
    if request.method == 'POST':
        title_of_interest = request.form.get('title')
        # Query TMDB for data
        movies = search_tmdb_for(title_of_interest)
        return render_template('select.html', movies=movies)

    return render_template('add.html', form=form)


@app.route("/delete")
def delete_movie():
    movie_id = request.args.get('id')
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/update", methods=['GET', 'POST'])
def update():
    form = RateMovieForm()
    movie_id = request.args.get('id')
    movie_to_update = Movie.query.get(movie_id)
    if form.validate_on_submit():
        new_rating = float(request.form.get('new_rating'))
        new_review = request.form.get('new_review')
        movie_to_update.rating = new_rating
        movie_to_update.review = new_review
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('edit.html', form=form, movie=movie_to_update)


@app.route("/")
def home():
    movies = Movie.query.all()
    return render_template("index.html", movies=movies)


if __name__ == '__main__':
    app.run(debug=True)
