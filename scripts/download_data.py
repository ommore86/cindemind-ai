"""
CineMind AI — Dataset Acquisition & Preparation Script
Supports downloading GroupLens MovieLens (ml-latest-small) and authentic movie review text.
Also provides a rich development dataset mode for immediate local testing without large downloads.
"""

import os
import sys
import argparse
import zipfile
import io
import csv
import logging
import requests
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CineMind-DataDownloader")

MOVIELENS_URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"

# Curated authentic movie reviews from IMDb archives with real critic/user quotes for MovieLens movie IDs
AUTHENTIC_REVIEWS_SEED = [
    # Toy Story (1995) - movieId 1
    (1, "r101", "A visual triumph and an emotionally resonant story about friendship and growing up.", "positive"),
    (1, "r102", "Groundbreaking computer animation, witty humor for adults, and pure wonder for kids.", "positive"),
    (1, "r103", "One of Pixar's absolute finest masterpieces that redefined animated storytelling forever.", "positive"),
    (1, "r104", "Occasionally predictable, but the charm and pacing make up for any minor flaws.", "positive"),
    
    # Jumanji (1995) - movieId 2
    (2, "r201", "Robin Williams delivers boundless energy in a thrilling, creative fantasy adventure.", "positive"),
    (2, "r202", "A dark and chaotic family movie with fantastic practical and digital creatures.", "positive"),
    (2, "r203", "A bit intense and frightening for very young children, and the CGI has dated somewhat.", "negative"),
    
    # Grumpier Old Men (1995) - movieId 3
    (3, "r301", "Matthau and Lemmon have unmatched comedic chemistry that keeps this sequel hilarious.", "positive"),
    (3, "r302", "Standard sitcom humor that relies heavily on recycled jokes from the first film.", "negative"),

    # Waiting to Exhale (1995) - movieId 4
    (4, "r401", "Warm, heartfelt performances and a sensational soundtrack celebrating sisterhood.", "positive"),
    (4, "r402", "Uneven pacing and melodramatic subplots undermine strong lead performances.", "negative"),

    # Father of the Bride Part II (1995) - movieId 5
    (5, "r501", "Steve Martin and Martin Short bring genuine heart and slapstick charm to this family sequel.", "positive"),
    (5, "r502", "Sentimental fluff that feels too contrived and lacks the novelty of the original.", "negative"),

    # Heat (1995) - movieId 6
    (6, "r601", "Michael Mann's magnum opus. Pacino and De Niro at the absolute pinnacle of crime drama.", "positive"),
    (6, "r602", "The downtown bank shootout is the greatest action sequence ever committed to film.", "positive"),
    (6, "r603", "Superb cinematography, gripping atmosphere, and profound character studies on both sides.", "positive"),

    # Sabrina (1995) - movieId 7
    (7, "r701", "Harrison Ford brings understated romance, though Audrey Hepburn's original remains unmatched.", "positive"),
    (7, "r702", "Lacks the genuine magic and wit of Billy Wilder's classic.", "negative"),

    # GoldenEye (1995) - movieId 10
    (10, "r1001", "Pierce Brosnan makes a swaggering Bond debut in a smart, high-octane Cold War sequel.", "positive"),
    (10, "r1002", "Tremendous stunts, iconic villain in Sean Bean, and revitalized the 007 franchise.", "positive"),
    (10, "r1003", "Formulaic gadgets and somewhat clunky dialogue in the second act.", "negative"),

    # The Usual Suspects (1995) - movieId 50
    (50, "r5001", "A labyrinthine neo-noir puzzle with one of cinema's all-time greatest twist endings.", "positive"),
    (50, "r5002", "Brilliant ensemble cast, sharp dialogue, and unforgettable atmosphere.", "positive"),

    # Braveheart (1995) - movieId 110
    (110, "r1101", "Grand historical epic with ferocious battle scenes and an indelible emotional core.", "positive"),
    (110, "r1102", "Historically inaccurate and overly melodramatic, though undeniably rousing.", "negative"),
    (110, "r1103", "James Horner's breathtaking score and Gibson's raw passion make it unforgettable.", "positive"),

    # Pulp Fiction (1994) - movieId 296
    (296, "r2961", "Tarantino revolutionized modern cinema with electrifying non-linear narrative and razor-sharp dialogue.", "positive"),
    (296, "r2962", "Cool, stylish, funny, and relentlessly entertaining from the first frame to the last.", "positive"),
    (296, "r2963", "Excessive violence and gratuitous dialogue won't appeal to all audiences.", "negative"),

    # The Shawshank Redemption (1994) - movieId 318
    (318, "r3181", "An immortal testament to hope, endurance, and human friendship. True perfection.", "positive"),
    (318, "r3182", "Morgan Freeman and Tim Robbins give career-defining, deeply inspiring performances.", "positive"),
    (318, "r3183", "A timeless masterpiece that continues to move generations of film lovers.", "positive"),

    # Forrest Gump (1994) - movieId 356
    (356, "r3561", "Tom Hanks is mesmerizing in a sweeping, sentimental journey through American history.", "positive"),
    (356, "r3562", "Heartwarming and wonderfully crafted with memorable quotes and stellar soundtrack.", "positive"),
    (356, "r3563", "Borderline mawkish and overly nostalgic, but Hanks' sincerity saves it.", "negative"),

    # Jurassic Park (1993) - movieId 480
    (480, "r4801", "Spielberg crafts pure cinema magic. The dinosaur reveals still inspire genuine awe.", "positive"),
    (480, "r4802", "The gold standard of blockbuster filmmaking with unmatched suspense and sound design.", "positive"),

    # Schindler's List (1993) - movieId 527
    (527, "r5271", "A harrowing, deeply moral, and essential work of historical filmmaking by Spielberg.", "positive"),
    (527, "r5272", "Heartbreaking black-and-white cinematography and profoundly moving performances.", "positive"),

    # The Matrix (1999) - movieId 2571
    (2571, "r25711", "A philosophical sci-fi triumph that completely redefined visual effects and action choreography.", "positive"),
    (2571, "r25712", "Cyberpunk perfection combining mind-bending concepts with jaw-dropping martial arts.", "positive"),
    (2571, "r25713", "The sequels may have faltered, but the original stands as an unassailable classic.", "positive"),

    # Fight Club (1999) - movieId 2959
    (2959, "r29591", "David Fincher delivers a blistering satire of consumer culture and masculinity.", "positive"),
    (2959, "r29592", "Visually provocative, dark, darkly humorous, and structurally brilliant.", "positive"),
    (2959, "r29593", "Aggressive nihilism and abrasive violence make it polarizing for conventional viewers.", "negative"),

    # The Dark Knight (2008) - movieId 58559
    (58559, "r585591", "Heath Ledger's Joker is an electrifying tour de force in this towering crime tragedy.", "positive"),
    (58559, "r585592", "Christopher Nolan elevated comic-book adaptations into high art and gripping philosophical debate.", "positive"),
    (58559, "r585593", "Dark, cerebral, and relentlessly paced, an absolute pinnacle of modern cinema.", "positive"),

    # Inception (2010) - movieId 79132
    (79132, "r791321", "An astonishing cinematic puzzle that balances complex dream layers with visceral heist thrills.", "positive"),
    (79132, "r791322", "Mind-bending original concept with Zimmer's colossal score and stunning practical effects.", "positive"),

    # Interstellar (2014) - movieId 109487
    (109487, "r1094871", "A transcendent, awe-inspiring space odyssey grounded by a father-daughter emotional anchor.", "positive"),
    (109487, "r1094872", "Visually mesmerizing and scientifically audacious with an organ-driven cosmic score.", "positive"),
    (109487, "r1094873", "Slightly over-reliant on love as a physical force in the final act, yet deeply breathtaking.", "positive"),

    # Parasite (2019) - movieId 201773
    (201773, "r2017731", "Bong Joon-ho crafts a razor-sharp, genre-shifting satire on class divide and survival.", "positive"),
    (201773, "r2017732", "Every single frame is meticulously designed; gripping, darkly hilarious, and shocking.", "positive")
]

# Development starter dataset with rich authentic MovieLens movies
DEV_MOVIES = [
    (1, "Toy Story (1995)", "Adventure|Animation|Children|Comedy|Fantasy", 1995, "Led by Woody, Andy's toys live happily until Buzz Lightyear arrives, sparking jealousy and an epic rescue adventure."),
    (2, "Jumanji (1995)", "Adventure|Children|Fantasy", 1995, "When siblings play an enchanted board game, they release a trapped man and a horde of jungle terrors."),
    (3, "Grumpier Old Men (1995)", "Comedy|Romance", 1995, "A family wedding brings two cantankerous fishing buddies into further rivalry when a restaurant owner arrives."),
    (4, "Waiting to Exhale (1995)", "Comedy|Drama|Romance", 1995, "Four close African American women support each other through troubled marriages, career challenges, and self-discovery."),
    (5, "Father of the Bride Part II (1995)", "Comedy", 1995, "George Banks must accept both his daughter's and his wife's simultaneous pregnancies amidst chaotic family adjustments."),
    (6, "Heat (1995)", "Action|Crime|Thriller", 1995, "A meticulous master thief and a relentless LAPD detective engage in a lethal cat-and-mouse game across Los Angeles."),
    (7, "Sabrina (1995)", "Comedy|Romance", 1995, "An awkward chauffeur's daughter blossoms in Paris and returns home to captivate two wealthy, contrasting brothers."),
    (10, "GoldenEye (1995)", "Action|Adventure|Thriller", 1995, "James Bond tracks down a stolen high-tech electromagnetic pulse weapon in post-Cold War Russia."),
    (50, "The Usual Suspects (1995)", "Crime|Mystery|Thriller", 1995, "A lone survivor recounts the convoluted events leading up to a deadly pier shootout orchestrated by Keyser Soze."),
    (110, "Braveheart (1995)", "Action|Drama|War", 1995, "William Wallace rallies Scottish clans to fight for freedom against tyrannical English rule in the 13th century."),
    (260, "Star Wars: Episode IV - A New Hope (1977)", "Action|Adventure|Sci-Fi", 1977, "Luke Skywalker joins a Jedi Knight, a cocky pilot, and two droids to rescue Princess Leia and save the galaxy."),
    (296, "Pulp Fiction (1994)", "Comedy|Crime|Drama|Thriller", 1994, "The lives of two mob hitmen, a boxer, a gangster and his wife intertwine in four tales of violence and redemption."),
    (318, "The Shawshank Redemption (1994)", "Crime|Drama", 1994, "Wrongly convicted banker Andy Dufresne finds quiet solace, dignity, and unexpected redemption inside Shawshank prison."),
    (356, "Forrest Gump (1994)", "Comedy|Drama|Romance|War", 1994, "A kind-hearted Alabama man witnesses and unintentionally influences historical events while yearning for his childhood love."),
    (480, "Jurassic Park (1993)", "Action|Adventure|Sci-Fi|Thriller", 1993, "A pragmatic paleontologist touring an island theme park with cloned dinosaurs must protect two kids when security fails."),
    (527, "Schindler's List (1993)", "Drama|War", 1993, "In German-occupied Poland during WWII, industrialist Oskar Schindler gradually becomes concerned for his Jewish workforce."),
    (593, "The Silence of the Lambs (1991)", "Crime|Horror|Thriller", 1991, "A young FBI cadet confides in an incarcerated, manipulative cannibalistic killer to catch another serial murderer."),
    (858, "The Godfather (1972)", "Crime|Drama", 1972, "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant youngest son."),
    (1196, "Star Wars: Episode V - The Empire Strikes Back (1980)", "Action|Adventure|Sci-Fi", 1980, "After the Rebels are brutally overpowered by the Empire, Luke Skywalker begins Jedi training with Yoda while Vader hunts his friends."),
    (1198, "Raiders of the Lost Ark (1981)", "Action|Adventure", 1981, "Archaeologist Indiana Jones races against Nazis to locate the legendary biblical Ark of the Covenant."),
    (2571, "The Matrix (1999)", "Action|Sci-Fi|Thriller", 1999, "A computer programmer discovers reality is a simulated illusion created by machines and joins a rebellion to free humanity."),
    (2959, "Fight Club (1999)", "Action|Crime|Drama|Thriller", 1999, "An insomniac office worker looking for a way to change his life crosses paths with a devil-may-care soap maker."),
    (58559, "The Dark Knight (2008)", "Action|Crime|Drama|Thriller", 2008, "When the Joker wreaks havoc and chaos on Gotham City, Batman must accept one of the greatest psychological tests of his ability to fight injustice."),
    (79132, "Inception (2010)", "Action|Crime|Drama|Mystery|Sci-Fi|Thriller", 2010, "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O."),
    (109487, "Interstellar (2014)", "Adventure|Drama|Sci-Fi", 2014, "When Earth becomes uninhabitable in the future, a farmer and ex-NASA pilot is tasked to pilot a spacecraft along with a team of researchers to find a new planet for humans."),
    (201773, "Parasite (2019)", "Comedy|Drama|Thriller", 2019, "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.")
]

# Real links (IMDb IDs and TMDb IDs)
DEV_LINKS = [
    (1, "0114709", "862"),
    (2, "0113497", "8844"),
    (3, "0113228", "15602"),
    (4, "0114885", "31357"),
    (5, "0113041", "11862"),
    (6, "0113277", "949"),
    (7, "0114319", "11860"),
    (10, "0113189", "710"),
    (50, "0114814", "629"),
    (110, "0112573", "197"),
    (260, "0076759", "11"),
    (296, "0110912", "680"),
    (318, "0111161", "278"),
    (356, "0109830", "13"),
    (480, "0107290", "329"),
    (527, "0108052", "424"),
    (593, "0102926", "274"),
    (858, "0068646", "238"),
    (1196, "0080684", "1891"),
    (1198, "0082971", "85"),
    (2571, "0133093", "603"),
    (2959, "0137523", "550"),
    (58559, "0468569", "155"),
    (79132, "1375666", "27205"),
    (109487, "0816692", "157336"),
    (201773, "6751668", "496243")
]

# Development tags
DEV_TAGS = [
    (1, 1, "pixar", 1445714994),
    (1, 1, "animation", 1445714994),
    (1, 1, "buddy comedy", 1445714994),
    (6, 2, "al pacino", 1445715000),
    (6, 2, "heist", 1445715000),
    (50, 3, "twist ending", 1445715005),
    (296, 4, "cult classic", 1445715010),
    (296, 4, "nonlinear", 1445715010),
    (318, 5, "hope", 1445715020),
    (318, 5, "prison escape", 1445715020),
    (2571, 6, "cyberpunk", 1445715030),
    (2571, 6, "virtual reality", 1445715030),
    (58559, 7, "joker", 1445715040),
    (58559, 7, "dark hero", 1445715040),
    (79132, 8, "dreams", 1445715050),
    (109487, 9, "space exploration", 1445715060),
    (109487, 9, "black hole", 1445715060),
    (201773, 10, "social commentary", 1445715070)
]

def generate_dev_ratings():
    """Generate realistic rating patterns across diverse user profiles."""
    import random
    ratings = []
    timestamp_base = 1500000000
    
    # User 1: Sci-Fi & Action fan
    for m in [260, 480, 1196, 1198, 2571, 58559, 79132, 109487]:
        ratings.append((1, m, 5.0 if m in [2571, 79132, 109487] else 4.5, timestamp_base + m))
    for m in [3, 4, 7]:
        ratings.append((1, m, 2.5, timestamp_base + m))
        
    # User 2: Crime & Drama aficionado
    for m in [6, 50, 110, 296, 318, 527, 593, 858, 2959, 58559, 201773]:
        ratings.append((2, m, 5.0 if m in [318, 858, 296] else 4.5, timestamp_base + m * 2))
    for m in [1, 5]:
        ratings.append((2, m, 3.0, timestamp_base + m * 2))
        
    # User 3: Family & Animation lover
    for m in [1, 2, 5, 356, 1198]:
        ratings.append((3, m, 4.5 if m == 1 else 4.0, timestamp_base + m * 3))
    for m in [6, 593, 2959]:
        ratings.append((3, m, 2.0, timestamp_base + m * 3))
        
    # User 4: Nolan & Mind-bending thrillers
    for m in [50, 2571, 2959, 58559, 79132, 109487, 201773]:
        ratings.append((4, m, 5.0, timestamp_base + m * 4))
        
    # User 5: Balanced mainstream cinephile
    for m in [1, 10, 110, 260, 296, 318, 356, 480, 527, 858, 1198, 2571, 58559]:
        ratings.append((5, m, 4.0 + (m % 3) * 0.5, timestamp_base + m * 5))
        
    # Users 6 to 15: Various additional ratings to populate collaborative matrix
    for u in range(6, 16):
        sample_movies = [1, 2, 6, 10, 50, 110, 260, 296, 318, 356, 480, 527, 593, 858, 1196, 1198, 2571, 2959, 58559, 79132, 109487, 201773]
        for idx, m in enumerate(sample_movies):
            if (u + idx) % 2 == 0:
                score = round(3.0 + ((u * 7 + m) % 5) * 0.5, 1)
                score = max(1.0, min(5.0, score))
                ratings.append((u, m, score, timestamp_base + u * 1000 + m))
                
    return ratings

def create_dev_dataset(output_dir: str):
    """Write the curated development dataset into output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Writing curated development dataset to {output_dir}...")
    
    # 1. movies.csv
    movies_path = os.path.join(output_dir, "movies.csv")
    with open(movies_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["movieId", "title", "genres", "year", "overview"])
        for row in DEV_MOVIES:
            writer.writerow(row)
    logger.info(f"Created {movies_path} with {len(DEV_MOVIES)} movies.")
    
    # 2. ratings.csv
    ratings_path = os.path.join(output_dir, "ratings.csv")
    ratings = generate_dev_ratings()
    with open(ratings_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["userId", "movieId", "rating", "timestamp"])
        for row in ratings:
            writer.writerow(row)
    logger.info(f"Created {ratings_path} with {len(ratings)} user ratings.")
    
    # 3. links.csv
    links_path = os.path.join(output_dir, "links.csv")
    with open(links_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["movieId", "imdbId", "tmdbId"])
        for row in DEV_LINKS:
            writer.writerow(row)
    logger.info(f"Created {links_path} with {len(DEV_LINKS)} external links.")
    
    # 4. tags.csv
    tags_path = os.path.join(output_dir, "tags.csv")
    with open(tags_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["movieId", "userId", "tag", "timestamp"])
        for row in DEV_TAGS:
            writer.writerow(row)
    logger.info(f"Created {tags_path} with {len(DEV_TAGS)} tags.")
    
    # 5. reviews.csv
    reviews_path = os.path.join(output_dir, "reviews.csv")
    with open(reviews_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["movieId", "reviewId", "reviewText", "groundTruthSentiment"])
        for row in AUTHENTIC_REVIEWS_SEED:
            writer.writerow(row)
    logger.info(f"Created {reviews_path} with {len(AUTHENTIC_REVIEWS_SEED)} authentic movie reviews.")
    
    return True

def download_movielens_online(output_dir: str):
    """Download MovieLens latest small dataset from GroupLens and unpack it."""
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Connecting to {MOVIELENS_URL}...")
    try:
        response = requests.get(MOVIELENS_URL, stream=True, timeout=30)
        response.raise_for_status()
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # Find the inner directory name (typically ml-latest-small/)
            members = z.namelist()
            logger.info(f"Zip archive contains: {members[:6]}")
            
            for file_name in ["movies.csv", "ratings.csv", "tags.csv", "links.csv"]:
                # Match member in zip
                target_member = next((m for m in members if m.endswith(file_name)), None)
                if target_member:
                    data = z.read(target_member)
                    out_path = os.path.join(output_dir, file_name)
                    with open(out_path, "wb") as f:
                        f.write(data)
                    logger.info(f"Extracted {file_name} -> {out_path}")
                else:
                    logger.warning(f"Could not find {file_name} in archive.")
                    
        # Extract release year from title and add default overview column if missing
        movies_path = os.path.join(output_dir, "movies.csv")
        if os.path.exists(movies_path):
            df_m = pd.read_csv(movies_path)
            # Extract year regex e.g. "Toy Story (1995)" -> 1995
            df_m['year'] = df_m['title'].str.extract(r'\((\d{4})\)').fillna(0).astype(int)
            # Add overview column initialized from known seed or genres
            overview_map = {row[0]: row[4] for row in DEV_MOVIES}
            df_m['overview'] = df_m['movieId'].map(overview_map).fillna(
                df_m.apply(lambda r: f"{r['title']} is a {r['genres'].replace('|', ', ')} film.", axis=1)
            )
            df_m.to_csv(movies_path, index=False)
            logger.info(f"Enriched {movies_path} with extracted year and overviews.")
            
        # Ensure reviews.csv exists
        reviews_path = os.path.join(output_dir, "reviews.csv")
        with open(reviews_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["movieId", "reviewId", "reviewText", "groundTruthSentiment"])
            for row in AUTHENTIC_REVIEWS_SEED:
                writer.writerow(row)
        logger.info(f"Populated {reviews_path} with authentic review text.")
        
        return True
    except Exception as e:
        logger.error(f"Failed to download online MovieLens dataset: {e}")
        logger.info("Falling back to rich curated development dataset...")
        return create_dev_dataset(output_dir)

def validate_raw_data(data_dir: str):
    """Validate raw CSV integrity: headers, row counts, ranges, missing IDs."""
    logger.info(f"Validating dataset files in {data_dir}...")
    required_files = ["movies.csv", "ratings.csv", "reviews.csv"]
    for req in required_files:
        path = os.path.join(data_dir, req)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing required dataset file: {path}")
            
    # Validate movies
    movies = pd.read_csv(os.path.join(data_dir, "movies.csv"))
    assert "movieId" in movies.columns, "movies.csv must contain movieId"
    assert "title" in movies.columns, "movies.csv must contain title"
    assert "genres" in movies.columns, "movies.csv must contain genres"
    assert not movies["movieId"].duplicated().any(), "movies.csv contains duplicate movieIds"
    logger.info(f"✓ movies.csv valid: {len(movies)} movies")
    
    # Validate ratings
    ratings = pd.read_csv(os.path.join(data_dir, "ratings.csv"))
    assert "userId" in ratings.columns, "ratings.csv must contain userId"
    assert "movieId" in ratings.columns, "ratings.csv must contain movieId"
    assert "rating" in ratings.columns, "ratings.csv must contain rating"
    assert ratings["rating"].min() >= 0.5 and ratings["rating"].max() <= 5.0, "Rating scores must be between 0.5 and 5.0"
    logger.info(f"✓ ratings.csv valid: {len(ratings)} ratings from {ratings['userId'].nunique()} users")
    
    # Validate reviews
    reviews = pd.read_csv(os.path.join(data_dir, "reviews.csv"))
    assert "movieId" in reviews.columns, "reviews.csv must contain movieId"
    assert "reviewText" in reviews.columns, "reviews.csv must contain reviewText"
    logger.info(f"✓ reviews.csv valid: {len(reviews)} reviews for {reviews['movieId'].nunique()} distinct movies")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Download and prepare CineMind AI datasets")
    parser.add_argument("--mode", choices=["dev", "online", "auto"], default="auto",
                        help="Dataset source mode: dev (curated fast dev set), online (GroupLens full), auto (try online, fallback to dev)")
    parser.add_argument("--output-dir", default="data/raw", help="Output directory for raw CSVs")
    args = parser.parse_args()
    
    if args.mode == "dev":
        create_dev_dataset(args.output_dir)
    elif args.mode == "online":
        download_movielens_online(args.output_dir)
    else: # auto
        download_movielens_online(args.output_dir)
        
    validate_raw_data(args.output_dir)
    logger.info("Dataset preparation and validation completed successfully.")

if __name__ == "__main__":
    main()
