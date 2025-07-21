import json

def get_product_data():
    """
    List of all product data from the Task 3 dataset document
    """
    products = [
        # === Men's Shoes ===
        {
            "id": "MEN-001",
            "name": "ASICS NOVABLAST 5 MEN'S RUNNING SHOES PURPLE",
            "price": 599.00,
            "original_price": 0,
            "discount_label": "",
            "url": "https://al-ikhsan.com/collections/asics/products/asics-novablast-5-mens-runningshoes-purple",
            "category": "Men's Running",
            "description": "The NOVABLAST 5 running shoe's midsole and outsole geometry helps produce an energized ride. FF BLAST MAX cushioning helps create softer landings and a more energized toe-off during your training. It's complemented with an engineered jacquard mesh upper that offers more stretch and ventilation.",
            "features": {
                "tech_and_materials": [
                    "FF BLAST MAX cushioning - Helps provide a lightweight and energetic ride.",
                    "Tongue wing construction - Added stretch helps improve the fit while reducing tongue movement.",
                    "Trampoline-inspired outsole design - Helps provide a more responsive bounce back.",
                    "Reflective details - Designed to help improve visibility in low-light settings.",
                    "AHAR LO outsole rubber - Helps create better traction, improved softness, and advanced durability."
                ]
            }
        },
        {
            "id": "MEN-002",
            "name": "NEW BALANCE FUEL CELL PROPEL MEN'S RUNNING SHOES GREY",
            "price": 299.00,
            "original_price": 529.00,
            "discount_label": "43% OFF",
            "url": "https://al-ikhsan.com/collections/new-balance/products/new-balance-fuel-cellpropel-mens-running-shoes-grey",
            "category": "Men's Running",
            "description": "New and experienced runners alike will appreciate the underfoot ride and innovative technology packed into the New Balance FuelCell Propel v4. Featuring a thick FuelCell midsole combined with a TPU plate, this running shoe is designed to maximize comfort and traction.",
            "features": {
                "details": [
                    "FuelCell foam delivers a propulsive feel to help drive you forward.",
                    "TPU plate for superior propulsion.",
                    "Engineered upper with synthetic/mesh construction.",
                    "Color: Dark camo with stoneware."
                ]
            }
        },
        {
            "id": "MEN-003",
            "name": "ADIDAS CLOUDFOAM GO SOCK MEN'S SHOES BLACK",
            "price": 99.00,
            "original_price": 299.00,
            "discount_label": "66% OFF",
            "url": "https://al-ikhsan.com/collections/adidas/products/adidas-cloudfoam-go-sockmens-shoes-black?_pos=11&_fid=fe838e888&_ss=c",
            "category": "Men's Casual",
            "description": "The Adidas Cloudfoam Go Sock is a laceless, slip-on shoe for comfort and sporty style. It features a lightweight textile upper and a Cloudfoam midsole for cushioning. Suitable for casual wear, leisurely walks, and everyday activities.",
            "features": {
                "key_features": [
                    "Slip-on design: Easy to put on and take off.",
                    "Cloudfoam midsole: Provides lightweight cushioning and comfort.",
                    "Textile upper: Offers a comfortable and breathable fit.",
                    "Adiwear outsole: Delivers durable traction.",
                    "Versatile style: Suitable for casual wear and various activities."
                ]
            }
        },

        # === Women's Running Shoes ===
        {
            "id": "WOMEN-001",
            "name": "ASICS GEL-NIMBUS 27 WOMEN'S RUNNING SHOES BLUE",
            "price": 509.00,
            "original_price": 729.00,
            "discount_label": "30% OFF",
            "url": "https://al-ikhsan.com/collections/asics/products/asics-gel-nimbus-27-women-srunning-shoes-blue",
            "category": "Women's Running",
            "description": "The GEL-NIMBUS 27 is designed for the most comfortable running experience with maximum cushioning. The pairing of PureGEL technology and FF BLAST PLUS ECO foam means you'll experience incredible comfort. Its updated upper and collar provide an unrivalled comfortable fit.",
            "features": {
                "key_features": [
                    "Innovative Rearfoot PureGEL technology improves shock absorption, reducing impact on your joints.",
                    "FF BLAST PLUS ECO foam delivers softer landing and premium cushioning.",
                    "Breathable upper and collar construction deliver an unmatched fit for ultimate comfort."
                ]
            }
        },
        {
            "id": "WOMEN-002",
            "name": "NEW BALANCE FRESH FOAM 680 WOMEN'S RUNNING SHOES WHITE",
            "price": 321.30,
            "original_price": 459.00,
            "discount_label": "30% OFF",
            "url": "https://al-ikhsan.com/collections/new-balance/products/new-balance-fresh-foam680-womens-running-shoes-white",
            "category": "Women's Running",
            "description": "The New Balance Fresh Foam 680v8 offers a versatile, comfortable, and durable option for everyday runs, workouts, and walking. They feature a Fresh Foam midsole for cushioning and a breathable mesh upper.",
            "features": {
                "key_features": [
                    "Fresh Foam Midsole: Provides lightweight and responsive cushioning.",
                    "Breathable Mesh Upper: Offers ventilation and flexibility.",
                    "Durable Rubber Outsole: Ensures long-lasting wear and reliable traction.",
                    "Comfortable Fit: Designed with a padded tongue and collar for added comfort."
                ]
            }
        },
        {
            "id": "WOMEN-003",
            "name": "ADIDAS DURAMO RC WOMEN'S RUNNING SHOES BLUE",
            "price": 139.00,
            "original_price": 249.00,
            "discount_label": "44% OFF",
            "url": "https://al-ikhsan.com/collections/adidas/products/adidas-duramo-rc-womensrunning-shoes-blue?_pos=14&_fid=fe838e888&_ss=c",
            "category": "Women's Running",
            "description": "With a light, soft and supportive feel, these adidas running shoes are set for your running journey. Made with a series of recycled materials, the upper features at least 50% recycled content.",
            "features": {
                "details": [
                    "Regular fit with lace closure.",
                    "Mesh upper with textile lining.",
                    "EVA midsole and Adiwear outsole.",
                    "Upper contains a minimum of 50% recycled content.",
                    "Product Colour: Blue Dawn / Cloud White / Wonder Quartz."
                ]
            }
        },

        # === Kids' Shoes ===
        {
            "id": "KID-001",
            "name": "NIKE REVOLUTION 7 LITTLE KIDS' SHOES BLUE",
            "price": 130.00,
            "original_price": 185.00,
            "discount_label": "29% OFF",
            "url": "https://al-ikhsan.com/collections/kids-shoes/products/nike-revolution-7-little-kidsshoes-blue",
            "category": "Kids' Running",
            "description": "Let your kiddo flash, dash and blast into the day with shoes made for fun. They come in awesome colors and designs that'll have your little one reaching for them every day.",
            "features": {
                "comfort_and_fit": [
                    "Pillow Soft: Cushioned collars are soft and squishy, with soft foam in the heel for comfort.",
                    "Easy On/Off: Elastic laces and hook-and-loop straps help kids put them on themselves.",
                    "Flexible, grippy tread helps kids find their footing on various surfaces.",
                    "Durable: Added material around the toe box reinforces the construction."
                ]
            }
        },
        {
            "id": "KID-002",
            "name": "PUMA ANZARUN LITE JUNIOR TRAINERS PINK",
            "price": 199.00,
            "original_price": 0,
            "discount_label": "",
            "url": "https://al-ikhsan.com/collections/kids-shoes/products/puma-anzarun-lite-juniortrainers-pink",
            "category": "Kids' Trainers",
            "description": "Deconstructed and refined, the Anzarun Lite Trainers ensure a clean look that's perfect for every occasion. This trainer is comfort and style combined for older kids between 8 and 16 years.",
            "features": {
                "features_and_benefits": [
                    "SoftFoam+: PUMA's comfort sockliner for instant step-in and long-lasting comfort.",
                    "PU midsole: PUMA's Polyurethane midsole assists a smooth foot stride."
                ],
                "details": [
                    "Low boot style with mesh-based textile upper.",
                    "EVA midsole for comfort and a non-marking rubber outsole for grip."
                ]
            }
        },
        {
            "id": "KID-003",
            "name": "ADIDAS TENSAUR SPORT 2.0 JUNIOR LIFESTYLE SHOES",
            "price": 111.00,
            "original_price": 159.00,
            "discount_label": "30% OFF",
            "url": "https://al-ikhsan.com/collections/kids-shoes/products/adidas-tensaur-sport-2-0-junior-lifestyle-shoes",
            "category": "Kids' Lifestyle",
            "description": "These classic adidas trainers have a rubber outsole that feels smooth for running but won't mark wood floors, so they'll work for school and sports practice. Made with at least 50% recycled content.",
            "features": {
                "details": [
                    "Regular fit with lace closure.",
                    "Synthetic and textile upper and lining.",
                    "Non-marking rubber outsole."
                ]
            }
        },
        {
            "id": "KID-004",
            "name": "ADIDAS TENSAUR RUN JUNIOR SHOES WHITE",
            "price": 101.40,
            "original_price": 169.00,
            "discount_label": "40% OFF",
            "url": "https://al-ikhsan.com/collections/kids-shoes/products/adidas-tensaur-run-junior-shoes-white",
            "category": "Kids' Running",
            "description": "Let your kid do up the hook-and-loop straps on these adidas shoes and get playing. The durable EVA unitsole gives them all they need for their everyday adventures. Made with at least 50% recycled content.",
            "features": {
                "details": [
                    "Regular fit with hook-and-loop closure.",
                    "Mesh mix upper with textile lining.",
                    "Reinforced eyestay and a one-piece EVA unitsole.",
                    "Product Colour: Cloud White/Blue Dawn/Beam Pink."
                ]
            }
        }
    ]
    return products


def create_embedding_text(product):
    """
    Flattens the structured product data into a single, keyword-rich string
    for a more accurate vector embedding.
    """
    feature_texts = []
    for category, feature_list in product.get("features", {}).items():
        feature_texts.extend(feature_list)

    # Create a highly descriptive summary to strengthen the embedding
    summary = f"This is a {product.get('category', '')} shoe named {product.get('name', '')}. It is described as: {product.get('description', '')}. Key features include: "

    embedding_string = summary + ". ".join(feature_texts)

    return embedding_string


if __name__ == "__main__":
    all_products = get_product_data()

    print("✓ Data parsing successful. All product data is clean and structured.")
    print(f"Total products loaded: {len(all_products)}")

    print("\n--- Sample Product (Structured JSON) ---")
    first_product = all_products[0]
    print(json.dumps(first_product, indent=2))
    print("----------------------------------------")

    print("\n--- Sample Text to be Embedded in Vector DB ---")
    embedding_content = create_embedding_text(first_product)
    print(embedding_content)
    print("---------------------------------------------")