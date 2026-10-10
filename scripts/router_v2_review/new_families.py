# ruff: noqa: E501  (text data: long strings are intentional)
# Decision 2: general questions where a small real-world step genuinely helps.
# Each family: five wordings (normal, hinglish, short, contextual, rephrased) sharing one target.
# Topics were checked against every test set (sealed, regression, golden, probe, guard sets) so
# none of them repeats a test question.
NEW_FAMILIES = [
    {
        "topic": "weather science",
        "route": "AI",
        "reason": "Why clouds change colour is basic weather science that can be explained directly.",
        "answer": "Cloud droplets are large enough to scatter all colours of sunlight about equally, so thin clouds look white. Thick rain clouds let less light through and are often shaded by cloud above, so their bases look grey or dark.",
        "outdoor_action": "Next time clouds build up, compare the colour of a thin cloud with the base of a thick one.",
        "questions": [
            "Why do clouds look white but turn grey before rain?",
            "Baadal safed kyun dikhte hain aur barish se pehle grey kyun ho jaate hain?",
            "why clouds white then grey",
            (
                "Why do clouds look white but turn grey before rain?",
                "it's getting cloudy here in Belagavi",
            ),
            "What makes rain clouds look grey?",
        ],
    },
    {
        "topic": "physics",
        "route": "AI",
        "reason": "Why a stick looks bent in water is basic optics that can be explained directly.",
        "answer": "Light travels more slowly in water than in air, so it bends as it crosses the surface. Your eyes assume light travels in straight lines, so the part under water appears shifted and the stick looks bent at the waterline.",
        "outdoor_action": "From a safe edge of a calm pond, or with a bucket of water, dip a straight stick and look at it from the side.",
        "questions": [
            "Why does a stick look bent when half of it is in water?",
            "Paani mein aadhi dubi stick tedhi kyun dikhti hai?",
            "stick looks bent in water",
            (
                "Why does a stick look bent when half of it is in water?",
                "saw it while fishing with my uncle in Alappuzha",
            ),
            "Why does a straight stick look broken in water?",
        ],
    },
    {
        "topic": "finance concept",
        "route": "AI",
        "reason": "How inflation affects savings is a general money concept that doesn't need a live check.",
        "answer": "Inflation means prices rise over time, so the same money buys a little less each year. If your savings earn less interest than the inflation rate, their real value falls even though the balance grows. Comparing the two rates shows whether your savings are keeping up.",
        "outdoor_action": "Next time you shop, compare today's price of something you buy often with what you paid a year ago.",
        "questions": [
            "How does inflation affect my savings?",
            "Inflation meri savings ko kaise affect karta hai?",
            "inflation savings effect",
            (
                "How does inflation affect my savings?",
                "started saving from my first salary in Noida",
            ),
            "Does inflation eat into money I keep in the bank?",
        ],
    },
    {
        "topic": "plant science",
        "route": "AI",
        "reason": "Why leaves are green and turn yellow is stable plant science.",
        "answer": "Leaves look green because chlorophyll absorbs red and blue light and reflects green. When a leaf ages, or a tree prepares to shed it, the chlorophyll breaks down and yellow and orange pigments that were there all along become visible.",
        "outdoor_action": "On a walk, compare a young leaf and an older leaf on the same tree and notice the difference in colour.",
        "questions": [
            "Why are leaves green, and why do they turn yellow?",
            "Patte hare kyun hote hain aur baad mein peele kyun ho jaate hain?",
            "why leaves turn yellow",
            (
                "Why are leaves green, and why do they turn yellow?",
                "noticed it on my street in Dehradun",
            ),
            "What makes leaves green and later yellow?",
        ],
    },
    {
        "topic": "everyday skill",
        "route": "AI",
        "reason": "Reading a nutrition label is general know-how that works for any pack.",
        "answer": "Start with the serving size, then compare values per 100 g so different packs are comparable. Look at sugar, salt or sodium, and saturated fat. The ingredient list is ordered from most to least by weight, so the first few items matter most.",
        "outdoor_action": "At a grocery shop, compare the sugar per 100 g on two similar snacks before choosing one.",
        "questions": [
            "How do I read a nutrition label on a food packet?",
            "Food packet ka nutrition label kaise padhun?",
            "read nutrition label",
            (
                "How do I read a nutrition label on a food packet?",
                "trying to eat better, shopping in Vadodara",
            ),
            "What should I look at first on a nutrition label?",
        ],
    },
    {
        "topic": "physics",
        "route": "AI",
        "reason": "How rainbows form is basic optics that can be explained directly.",
        "answer": "Sunlight enters raindrops, bends, reflects off the back of the drop, and bends again on the way out. Each colour bends by a slightly different amount, so the light spreads into bands. You see a rainbow with the sun behind you and rain in front of you.",
        "outdoor_action": "After a shower when the sun comes out, stand with the sun behind you and look toward the opposite side of the sky.",
        "questions": [
            "How does a rainbow form?",
            "Rainbow kaise banta hai?",
            "how rainbow forms",
            ("How does a rainbow form?", "saw one this morning in Thrissur"),
            "What actually creates a rainbow?",
        ],
    },
    {
        "topic": "astronomy",
        "route": "AI",
        "reason": "Why stars twinkle and planets don't is well-understood astronomy.",
        "answer": "Stars are so far away that each appears as a single point of light, and moving layers of air bend that light slightly, making it flicker. Planets are closer and appear as tiny discs, so the flicker averages out and they shine more steadily. Twinkling is strongest near the horizon.",
        "outdoor_action": "On a clear night, from a terrace or another safe spot, compare a bright star low in the sky with one high overhead.",
        "questions": [
            "Why do stars twinkle but planets usually don't?",
            "Taare timtimate kyun hain par planets kyun nahi?",
            "why stars twinkle",
            (
                "Why do stars twinkle but planets usually don't?",
                "stargazing from our rooftop in Bikaner",
            ),
            "What makes stars twinkle?",
        ],
    },
    {
        "topic": "nature knowledge",
        "route": "AI",
        "reason": "Telling moths from butterflies uses general, well-known features.",
        "answer": "Most butterflies fly by day, have thin antennae with a club at the tip, and rest with wings folded upright. Many moths fly at night, have feathery or tapering antennae, and rest with wings spread flat or tent-like. There are exceptions, so use several features together.",
        "outdoor_action": "In a garden by day or near a lit area in the evening, watch one insect at rest and check its antennae and wings.",
        "questions": [
            "How can I tell a moth from a butterfly?",
            "Moth aur butterfly mein fark kaise pehchanu?",
            "moth vs butterfly",
            (
                "How can I tell a moth from a butterfly?",
                "my son found one on our balcony in Coimbatore",
            ),
            "What's the easiest way to tell moths and butterflies apart?",
        ],
    },
    {
        "topic": "technology",
        "route": "AI",
        "reason": "How solar panels work is stable technology know-how.",
        "answer": "Solar panels are made of cells, usually silicon, that release electrons when sunlight hits them. The cells are wired so those electrons flow as direct current, and an inverter converts it to the alternating current used at home. Output depends on sunlight, panel angle and shade.",
        "outdoor_action": "When you pass a building with rooftop solar panels, notice which direction they face and whether anything shades them.",
        "questions": [
            "How do solar panels make electricity?",
            "Solar panel bijli kaise banata hai?",
            "how solar panel works",
            (
                "How do solar panels make electricity?",
                "our society is thinking of installing them in Gurugram",
            ),
            "Can you explain how solar panels make power?",
        ],
    },
    {
        "topic": "measurement",
        "route": "AI",
        "reason": "Estimating distance by counting steps is a simple general method.",
        "answer": "Walk a known distance, such as a 100-metre stretch, at your normal pace and count your steps. Divide the distance by the number of steps to get your stride length. Multiply later step counts by that length to estimate distance.",
        "outdoor_action": "On a running track or a marked 100-metre stretch, count your steps once to find your stride length.",
        "questions": [
            "How can I measure distance by counting my steps?",
            "Kadam gin ke distance kaise nikalun?",
            "measure distance by steps",
            (
                "How can I measure distance by counting my steps?",
                "my phone pedometer seems off, I'm in Bhubaneswar",
            ),
            "Is there a simple way to estimate distance by walking?",
        ],
    },
    {
        "topic": "astronomy event",
        "route": "SEARCH",
        "reason": "Meteor shower peak dates change each year, so a current sky calendar is needed.",
        "search_query": "meteor shower visible from India this month peak date",
        "outdoor_action": "If a shower is listed, watch from a safe open spot such as a terrace on the peak night, away from bright lights.",
        "questions": [
            "Is there a meteor shower visible from India this month?",
            "Is month India se koi meteor shower dikhega kya?",
            "meteor shower india this month",
            (
                "Is there a meteor shower visible from India this month?",
                "want to watch one with my kids",
            ),
            "When is the next meteor shower I can see from India?",
        ],
    },
]
