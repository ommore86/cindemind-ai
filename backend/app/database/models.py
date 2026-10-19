"""
CineMind AI — Database Models
SQLAlchemy Declarative Models for Movies, Ratings, Reviews, Sentiment Aggregates, and Evaluations.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Movie(Base):
    __tablename__ = "movies"
    
    movie_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    genres = Column(String(255), nullable=False)
    year = Column(Integer, nullable=True)
    overview = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    avg_rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    weighted_score = Column(Float, default=0.0)
    imdb_id = Column(String(50), nullable=True)
    tmdb_id = Column(String(50), nullable=True)
    poster_url = Column(String(500), nullable=True)
    
    # Relationships
    ratings = relationship("Rating", back_populates="movie", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="movie", cascade="all, delete-orphan")
    sentiment_aggregate = relationship("MovieSentimentAggregate", back_populates="movie", uselist=False, cascade="all, delete-orphan")


class Rating(Base):
    __tablename__ = "ratings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey("movies.movie_id"), nullable=False, index=True)
    rating = Column(Float, nullable=False)
    timestamp = Column(Integer, nullable=True)
    
    movie = relationship("Movie", back_populates="ratings")
    
    __table_args__ = (
        Index("idx_user_movie", "user_id", "movie_id", unique=True),
    )


class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    movie_id = Column(Integer, ForeignKey("movies.movie_id"), nullable=False, index=True)
    review_id = Column(String(100), nullable=True)
    review_text = Column(Text, nullable=False)
    ground_truth_sentiment = Column(String(20), nullable=True)
    predicted_sentiment = Column(String(20), nullable=True)
    sentiment_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    movie = relationship("Movie", back_populates="reviews")


class MovieSentimentAggregate(Base):
    __tablename__ = "movie_sentiment_aggregates"
    
    movie_id = Column(Integer, ForeignKey("movies.movie_id"), primary_key=True)
    analyzed_reviews = Column(Integer, default=0)
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    positive_ratio = Column(Float, default=0.0)
    aggregate_sentiment_score = Column(Float, default=0.0)
    average_confidence = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    movie = relationship("Movie", back_populates="sentiment_aggregate")


class ModelEvaluation(Base):
    __tablename__ = "model_evaluations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(100), nullable=False) # 'content_based', 'collaborative', 'hybrid'
    k_value = Column(Integer, default=10)
    precision_at_k = Column(Float, nullable=True)
    recall_at_k = Column(Float, nullable=True)
    ndcg_at_k = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    mae = Column(Float, nullable=True)
    sample_size = Column(Integer, default=0)
    evaluated_at = Column(DateTime, default=datetime.utcnow)
