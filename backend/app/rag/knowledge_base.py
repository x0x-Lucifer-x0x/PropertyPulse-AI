"""
Static knowledge-base documents for RAG: general real-estate concepts and
Bangalore locality overviews. This is general domain knowledge, not
specific claims about any listed property — property facts always come
from the database via search_properties / get_property_details, never
from here.
"""

STATIC_DOCS = [
    {
        "id": "kb-rera",
        "title": "What RERA means for a buyer",
        "text": (
            "RERA (Real Estate Regulatory Authority) registration is mandatory "
            "for most residential projects in India above a certain size. A "
            "RERA number lets a buyer look up a project's approved plan, "
            "promised possession date, and the developer's track record on "
            "the state RERA website. Always ask for the RERA number before "
            "paying a booking amount, and verify it independently rather than "
            "taking a broker's word for it."
        ),
    },
    {
        "id": "kb-bhk",
        "title": "What BHK means",
        "text": (
            "BHK stands for Bedroom, Hall, Kitchen — the standard shorthand "
            "for apartment configuration in India. A 2BHK has two bedrooms "
            "plus a living/hall area and kitchen; a 3BHK has three bedrooms. "
            "It does not count bathrooms separately, so two 2BHK units from "
            "different builders can still differ in bathroom count and "
            "carpet area."
        ),
    },
    {
        "id": "kb-possession",
        "title": "Possession status: ready to move vs under construction vs new launch",
        "text": (
            "'Ready to move' means construction is complete and the unit can "
            "be registered and occupied immediately — usually priced higher "
            "per sq.ft. but with no construction-timeline risk. 'Under "
            "construction' projects are being built against a promised "
            "possession date and are typically cheaper, with payment tied to "
            "construction milestones. 'New launch' projects have just opened "
            "bookings and possession is furthest out, usually at the lowest "
            "entry price but with the most schedule uncertainty."
        ),
    },
    {
        "id": "kb-home-loan",
        "title": "How home loan EMIs work",
        "text": (
            "A home loan EMI (equated monthly installment) is calculated on "
            "the loan amount (property price minus down payment), the "
            "annual interest rate, and the loan tenure in years, using "
            "reducing-balance amortization — meaning the interest portion of "
            "each EMI shrinks over time while the principal portion grows. A "
            "larger down payment or shorter tenure lowers total interest "
            "paid but raises the monthly EMI; a longer tenure lowers the EMI "
            "but increases total interest paid over the life of the loan."
        ),
    },
    {
        "id": "kb-whitefield",
        "title": "Whitefield locality overview",
        "text": (
            "Whitefield is an established IT hub in east Bangalore, home to "
            "ITPL and many large tech campuses. It has good social "
            "infrastructure — malls, hospitals, international schools — and "
            "reasonable Metro connectivity via the Purple Line extension. "
            "Popular with IT professionals working nearby who want to avoid "
            "a long commute to the eastern tech corridor."
        ),
    },
    {
        "id": "kb-sarjapur",
        "title": "Sarjapur / Sarjapur Road locality overview",
        "text": (
            "Sarjapur Road connects several major tech parks (including "
            "campuses near Wipro and other large employers) and has seen "
            "heavy new residential supply over the last decade. It's popular "
            "with young tech families for its newer gated communities, "
            "though peak-hour traffic on the main road can be heavy and "
            "Metro connectivity is still developing."
        ),
    },
    {
        "id": "kb-electronic-city",
        "title": "Electronic City locality overview",
        "text": (
            "Electronic City is one of Bangalore's oldest IT/ITES hubs in "
            "the south, split into Phase 1 and Phase 2. It tends to offer "
            "relatively affordable housing compared to the eastern corridor, "
            "with the Elevated Expressway easing the commute to central "
            "Bangalore, and Metro connectivity now extending into the area."
        ),
    },
    {
        "id": "kb-koramangala",
        "title": "Koramangala locality overview",
        "text": (
            "Koramangala is a central, well-established residential and "
            "commercial neighborhood popular with young professionals and "
            "startups, known for its restaurants, nightlife, and walkable "
            "layout. It commands some of the higher per-sq.ft. prices in the "
            "city given its central location and mature infrastructure."
        ),
    },
    {
        "id": "kb-hsr-layout",
        "title": "HSR Layout locality overview",
        "text": (
            "HSR Layout is a planned, sector-based residential neighborhood "
            "close to the Outer Ring Road tech corridor and Koramangala. "
            "It's popular with tech professionals and startup employees for "
            "its mix of apartments, good civic planning, and proximity to "
            "Sector 1's cafes and coworking spaces."
        ),
    },
    {
        "id": "kb-bellandur",
        "title": "Bellandur locality overview",
        "text": (
            "Bellandur sits along the Outer Ring Road tech corridor, close "
            "to several major IT campuses, and has a large concentration of "
            "gated apartment communities. Commute times within the ORR "
            "corridor can be affected by traffic during peak hours."
        ),
    },
    {
        "id": "kb-yelahanka",
        "title": "Yelahanka locality overview",
        "text": (
            "Yelahanka is in north Bangalore, closer to Kempegowda "
            "International Airport, and has seen growing residential "
            "development as north Bangalore's infrastructure improves. It "
            "tends to offer more space for the price than the eastern IT "
            "corridor, appealing to buyers prioritizing airport proximity "
            "or a quieter, less dense area."
        ),
    },
    {
        "id": "kb-hebbal",
        "title": "Hebbal locality overview",
        "text": (
            "Hebbal is a well-connected north Bangalore locality near "
            "Manyata Tech Park, with good arterial road and flyover "
            "connectivity toward both the airport and the city center. It "
            "tends to have a mix of premium and mid-range residential "
            "developments given its proximity to a major employment hub."
        ),
    },
    {
        "id": "kb-devanahalli",
        "title": "Devanahalli locality overview",
        "text": (
            "Devanahalli, near Kempegowda International Airport, is one of "
            "north Bangalore's fastest-developing corridors, with new "
            "residential and aerotropolis-linked commercial development. "
            "It suits buyers prioritizing airport access or longer-term "
            "appreciation potential in an emerging area over immediate "
            "proximity to established IT hubs."
        ),
    },
    {
        "id": "kb-jp-nagar",
        "title": "JP Nagar locality overview",
        "text": (
            "JP Nagar is a well-established south Bangalore residential "
            "area with mature social infrastructure — schools, hospitals, "
            "and retail along Bannerghatta Road — and reasonable Metro "
            "connectivity via the Green Line. It suits buyers who want a "
            "settled neighborhood rather than a newer, still-developing one."
        ),
    },
]
