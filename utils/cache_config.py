DEFAULT_CACHE_TTL = 3600
DEFAULT_CACHE_SIZE = 100

CACHE_SETTINGS = {
    'asteroids': {
        'ttl': 12 * 3600,
        'max_size': 50
    },
    'mars_photos': {
        'ttl': 7 * 24 * 3600,
        'max_size': 200
    },
    'earth_imagery': {
        'ttl': 30 * 24 * 3600,
        'max_size': 100
    },
    'planet_images': {
        'ttl': 30 * 24 * 3600,
        'max_size': 100
    }
}
