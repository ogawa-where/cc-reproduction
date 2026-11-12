"""The CROQ taxonomy: 11 domains and 66 subtopics, copied from Table 5 of the paper."""
TAXONOMY = {
    "Beliefs": ["Religion & Spirituality", "Values & Ethics", "Symbolism", "Mythology & Folklore", "Gender Roles"],
    "Social": ["Family & Social Roles", "Community Life", "Manners & Etiquette", "Work Culture", "Conflict Resolution"],
    "Education": ["Language & Communication", "Education Systems", "Technology & Tools", "Knowledge Transmission",
                  "Science & Philosophy"],
    "Arts": ["Music", "Dance", "Art", "Literature & Storytelling", "Theater & Performance", "Film & Cinema",
             "Crafts & Handicrafts", "Jewelry & Body Decoration", "Architecture & Housing"],
    "Food": ["Food & Cuisine", "Traditional Beverages", "Recreation & Leisure", "Sports & Games", "Life-Cycle Rituals",
             "Festivals & Celebrations"],
    "Geography": ["Climate & Environment", "Topography & Land Use", "Rural vs Urban Culture", "Regional Identity",
                  "Borders & Territory", "Migration & Diaspora", "Relationship with Nature"],
    "Politics": ["Government Systems", "Law & Legal Traditions", "Civic Values & Participation",
                 "Freedom of Expression", "Colonial History & Influence", "Power & Hierarchy",
                 "Human Rights & Social Movements"],
    "Health": ["Health Practices", "Public Health", "Wellbeing & Lifestyle", "Birth & Reproductive Health"],
    "Media": ["Local Media", "Digital Media", "Entertainment Industries", "News & Information", "Popular Culture",
              "Gaming & Interactive Media"],
    "History": ["Historical Events", "Historical Figures", "Cultural Memory", "Colonialism & Resistance",
                "National Narratives", "Heritage & Preservation"],
    "Economy": ["Key Industries", "Trade & Exchange", "Labor & Employment", "Wealth & Inequality",
                "Economic Growth & Development", "Globalization & Cultural Economy"],
}
EXAMPLES = {  # the paper's example question per domain (Section 3)
    "Beliefs": "What legends explain the land?", "Social": "What is the role of neighbors?",
    "Education": "What subjects are most valued?", "Arts": "What traditional dances exist?",
    "Food": "What foods are for daily meal?", "Geography": "What rivers influence settlements?",
    "Politics": "What political protests are common?", "Health": "What exercise routines are common?",
    "Media": "What film industries exist?", "History": "What historical tours exist?",
    "Economy": "What commodity markets exist?",
}
SUFFIX_EN = "Be brief. Choose yourself the place."
assert sum(len(v) for v in TAXONOMY.values()) == 66
