"""Curated registry of popular content creators, podcasters, and streamers."""
from typing import Dict, Any, Optional

CREATOR_REGISTRY: Dict[str, Dict[str, Any]] = {
    "rogan": {
        "name": "Joe Rogan",
        "handle": "@joerogan",
        "channel_url": "https://www.youtube.com/@joerogan/videos",
        "default_layout": "blur_bg",
        "category": "Podcast / Comedy / Philosophy",
        "hashtags": ["#joerogan", "#jre", "#podcast", "#shorts", "#viral"]
    },
    "mrbeast": {
        "name": "MrBeast",
        "handle": "@MrBeast",
        "channel_url": "https://www.youtube.com/@MrBeast/videos",
        "default_layout": "blur_bg",
        "category": "Entertainment / Challenges",
        "hashtags": ["#mrbeast", "#challenge", "#shorts", "#viral", "#entertainment"]
    },
    "huberman": {
        "name": "Andrew Huberman",
        "handle": "@hubermanlab",
        "channel_url": "https://www.youtube.com/@hubermanlab/videos",
        "default_layout": "blur_bg",
        "category": "Science / Health / Neuroscience",
        "hashtags": ["#hubermanlab", "#andrewhuberman", "#health", "#science", "#shorts"]
    },
    "theovon": {
        "name": "Theo Von",
        "handle": "@TheoVon",
        "channel_url": "https://www.youtube.com/@TheoVon/videos",
        "default_layout": "blur_bg",
        "category": "Comedy / Podcast",
        "hashtags": ["#theovon", "#thispastweekend", "#comedy", "#shorts", "#funny"]
    },
    "kaicenat": {
        "name": "Kai Cenat",
        "handle": "@KaiCenat",
        "channel_url": "https://www.youtube.com/@KaiCenat/videos",
        "default_layout": "blur_bg",
        "category": "Streaming / Entertainment",
        "hashtags": ["#kaicenat", "#amp", "#streamer", "#shorts", "#viral"]
    },
    "speed": {
        "name": "IShowSpeed",
        "handle": "@IShowSpeed",
        "channel_url": "https://www.youtube.com/@IShowSpeed/videos",
        "default_layout": "blur_bg",
        "category": "Streaming / Gaming / Entertainment",
        "hashtags": ["#ishowspeed", "#speed", "#streamer", "#shorts", "#viral"]
    },
    "lexfridman": {
        "name": "Lex Fridman",
        "handle": "@lexfridman",
        "channel_url": "https://www.youtube.com/@lexfridman/videos",
        "default_layout": "blur_bg",
        "category": "AI / Science / Podcast",
        "hashtags": ["#lexfridman", "#podcast", "#ai", "#science", "#shorts"]
    },
    "modernwisdom": {
        "name": "Chris Williamson (Modern Wisdom)",
        "handle": "@ChrisWillx",
        "channel_url": "https://www.youtube.com/@ChrisWillx/videos",
        "default_layout": "blur_bg",
        "category": "Self Improvement / Philosophy",
        "hashtags": ["#modernwisdom", "#chriswilliamson", "#psychology", "#shorts"]
    },
    "diaryofaceo": {
        "name": "Steven Bartlett (The Diary Of A CEO)",
        "handle": "@TheDiaryOfACEO",
        "channel_url": "https://www.youtube.com/@TheDiaryOfACEO/videos",
        "default_layout": "blur_bg",
        "category": "Business / Leadership / Mindset",
        "hashtags": ["#doac", "#stevenbartlett", "#business", "#mindset", "#shorts"]
    },
    "jordanpeterson": {
        "name": "Jordan B Peterson",
        "handle": "@JordanBPeterson",
        "channel_url": "https://www.youtube.com/@JordanBPeterson/videos",
        "default_layout": "blur_bg",
        "category": "Psychology / Philosophy",
        "hashtags": ["#jordanpeterson", "#psychology", "#philosophy", "#shorts"]
    },
    "impaulsive": {
        "name": "Impaulsive (Logan Paul)",
        "handle": "@impaulsive",
        "channel_url": "https://www.youtube.com/@impaulsive/videos",
        "default_layout": "blur_bg",
        "category": "Podcast / Pop Culture",
        "hashtags": ["#impaulsive", "#loganpaul", "#podcast", "#shorts"]
    },
    "asmongold": {
        "name": "Asmongold",
        "handle": "Asmongold TV",
        "channel_url": "https://www.youtube.com/channel/UCQeRaTukNYft1_6AZPACnog/videos",
        "default_layout": "blur_bg",
        "category": "Gaming / Reaction / Pop Culture",
        "hashtags": ["#asmongold", "#reaction", "#gaming", "#twitch", "#shorts", "#viral"]
    },
    "caseoh": {
        "name": "CaseOh",
        "handle": "@CaseOh_",
        "channel_url": "https://www.youtube.com/@CaseOh_/videos",
        "default_layout": "blur_bg",
        "category": "Streaming / Gaming / Comedy",
        "hashtags": ["#caseoh", "#gaming", "#streamer", "#twitch", "#shorts", "#funny"]
    },
    "penguinz0": {
        "name": "MoistCr1TiKaL (Charlie)",
        "handle": "@penguinz0",
        "channel_url": "https://www.youtube.com/@penguinz0/videos",
        "default_layout": "blur_bg",
        "category": "Commentary / Pop Culture / Humor",
        "hashtags": ["#moistcr1tikal", "#penguinz0", "#commentary", "#shorts", "#viral"]
    },
    "hormozi": {
        "name": "Alex Hormozi",
        "handle": "@AlexHormozi",
        "channel_url": "https://www.youtube.com/@AlexHormozi/videos",
        "default_layout": "blur_bg",
        "category": "Business / Wealth / Mindset",
        "hashtags": ["#alexhormozi", "#hormozi", "#business", "#money", "#wealth", "#shorts"]
    },
    "flagrant": {
        "name": "Andrew Schulz (Flagrant)",
        "handle": "FLAGRANT",
        "channel_url": "https://www.youtube.com/channel/UC5PstSsGrRwj2o6asQpC4Rg/videos",
        "default_layout": "blur_bg",
        "category": "Comedy / Podcast / Debates",
        "hashtags": ["#flagrant", "#andrewschulz", "#comedy", "#podcast", "#shorts"]
    },
    "pbd": {
        "name": "Patrick Bet-David (PBD Podcast)",
        "handle": "@PBDPodcast",
        "channel_url": "https://www.youtube.com/@PBDPodcast/videos",
        "default_layout": "blur_bg",
        "category": "Business / Politics / Current Affairs",
        "hashtags": ["#pbdpodcast", "#patrickbetdavid", "#business", "#politics", "#shorts"]
    },
    "rawtalk": {
        "name": "Bradley Martyn (Raw Talk)",
        "handle": "Raw Talk",
        "channel_url": "https://www.youtube.com/channel/UCSt7m67E9O8xONdHsNIy39A/videos",
        "default_layout": "blur_bg",
        "category": "Fitness / Podcast / Culture",
        "hashtags": ["#rawtalk", "#bradleymartyn", "#fitness", "#podcast", "#shorts"]
    },
    "xqc": {
        "name": "xQc",
        "handle": "@xQcOW",
        "channel_url": "https://www.youtube.com/@xQcOW/videos",
        "default_layout": "blur_bg",
        "category": "Streaming / Gaming / Reaction",
        "hashtags": ["#xqc", "#xqcow", "#streamer", "#kick", "#twitch", "#shorts"]
    },
    "sketch": {
        "name": "Sketch",
        "handle": "@thesketchreal",
        "channel_url": "https://www.youtube.com/@thesketchreal/videos",
        "default_layout": "blur_bg",
        "category": "Streaming / Gaming / Comedy",
        "hashtags": ["#sketch", "#whatsupbrother", "#streamer", "#gaming", "#shorts"]
    },
    "jocko": {
        "name": "Jocko Willink",
        "handle": "@JockoPodcastOfficial",
        "channel_url": "https://www.youtube.com/@JockoPodcastOfficial/videos",
        "default_layout": "blur_bg",
        "category": "Leadership / Military / Mindset",
        "hashtags": ["#jockowillink", "#jockopodcast", "#discipline", "#motivation", "#shorts"]
    },
    "fullsend": {
        "name": "Full Send Podcast (NELK)",
        "handle": "@FullSendPodcast",
        "channel_url": "https://www.youtube.com/@FullSendPodcast/videos",
        "default_layout": "blur_bg",
        "category": "Podcast / Entertainment / Comedy",
        "hashtags": ["#fullsend", "#nelk", "#nelkboys", "#podcast", "#shorts"]
    },
    "mkbhd": {
        "name": "Marques Brownlee (MKBHD)",
        "handle": "@mkbhd",
        "channel_url": "https://www.youtube.com/@mkbhd/videos",
        "default_layout": "blur_bg",
        "category": "Technology / Reviews / Innovation",
        "hashtags": ["#mkbhd", "#tech", "#smartphone", "#apple", "#shorts"]
    },
    "impacttheory": {
        "name": "Tom Bilyeu (Impact Theory)",
        "handle": "@TomBilyeu",
        "channel_url": "https://www.youtube.com/@TomBilyeu/videos",
        "default_layout": "blur_bg",
        "category": "Success / Mindset / Psychology",
        "hashtags": ["#impacttheory", "#tombilyeu", "#mindset", "#success", "#shorts"]
    },
    "markrober": {
        "name": "Mark Rober",
        "handle": "@MarkRober",
        "channel_url": "https://www.youtube.com/@MarkRober/videos",
        "default_layout": "blur_bg",
        "category": "Engineering / Science / Entertainment",
        "hashtags": ["#markrober", "#engineering", "#science", "#experiment", "#shorts"]
    },
    "veritasium": {
        "name": "Veritasium (Derek Muller)",
        "handle": "@veritasium",
        "channel_url": "https://www.youtube.com/@veritasium/videos",
        "default_layout": "blur_bg",
        "category": "Science / Physics / Curiosities",
        "hashtags": ["#veritasium", "#science", "#physics", "#discovery", "#shorts"]
    }
}

# User-friendly aliases
CREATOR_ALIASES: Dict[str, str] = {
    "ishowspeed": "speed",
    "speed": "speed",
    "kai": "kaicenat",
    "kaicenat": "kaicenat",
    "charlie": "penguinz0",
    "critikal": "penguinz0",
    "cr1tikal": "penguinz0",
    "moist": "penguinz0",
    "moistcr1tikal": "penguinz0",
    "alex": "hormozi",
    "alexhormozi": "hormozi",
    "hormozi": "hormozi",
    "schulz": "flagrant",
    "andrewschulz": "flagrant",
    "flagrant": "flagrant",
    "patrick": "pbd",
    "patrickbetdavid": "pbd",
    "pbd": "pbd",
    "bradley": "rawtalk",
    "bradleymartyn": "rawtalk",
    "rawtalk": "rawtalk",
    "thesketchreal": "sketch",
    "sketch": "sketch",
    "jockowillink": "jocko",
    "jocko": "jocko",
    "nelk": "fullsend",
    "nelkboys": "fullsend",
    "fullsend": "fullsend",
    "marques": "mkbhd",
    "marquesbrownlee": "mkbhd",
    "mkbhd": "mkbhd",
    "tombilyeu": "impacttheory",
    "impacttheory": "impacttheory",
    "zackrawrr": "asmongold",
    "asmon": "asmongold",
    "asmongold": "asmongold",
    "doac": "diaryofaceo",
    "stevenbartlett": "diaryofaceo",
    "steven": "diaryofaceo",
    "chriswillx": "modernwisdom",
    "chriswilliamson": "modernwisdom",
    "chris": "modernwisdom",
    "joerogan": "rogan",
    "jre": "rogan",
    "loganpaul": "impaulsive",
    "logan": "impaulsive",
    "jordan": "jordanpeterson",
    "peterson": "jordanpeterson",
    "theo": "theovon",
    "beast": "mrbeast",
    "andrew": "huberman",
    "andrewhuberman": "huberman",
    "lex": "lexfridman"
}

def get_creator(key: str) -> Optional[Dict[str, Any]]:
    """Look up a creator preset by key, alias, or partial name."""
    clean = key.strip().lower().replace(" ", "").replace("@", "")
    
    # 1. Check exact alias
    if clean in CREATOR_ALIASES:
        target_key = CREATOR_ALIASES[clean]
        if target_key in CREATOR_REGISTRY:
            return CREATOR_REGISTRY[target_key]

    # 2. Check exact key in registry
    if clean in CREATOR_REGISTRY:
        return CREATOR_REGISTRY[clean]
    
    # 3. Check substring match in registry keys or names
    for k, v in CREATOR_REGISTRY.items():
        if clean in k or clean in v["name"].lower().replace(" ", ""):
            return v
            
    return None

def list_creators():
    """Returns list of all available creator presets."""
    return [
        {
            "key": k,
            "name": v["name"],
            "handle": v["handle"],
            "category": v.get("category", ""),
            "layout": v["default_layout"]
        }
        for k, v in CREATOR_REGISTRY.items()
    ]
