import os
import base64
import mimetypes
from flask import Flask, request, render_template, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
from groq import Groq
from dotenv import load_dotenv
import traceback
import re
import json
import time

# --- SETUP ---
load_dotenv()
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER): 
    os.makedirs(UPLOAD_FOLDER)
    
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# --- SECTOR CONFIGURATION ---
SECTOR_CONFIG = {
    "real_estate": {
        "name": "Real Estate",
        "category_check": "real estate, properties, apartments, houses, land, construction",
        "screening_focus": ["RERA Number", "Location", "Property Type", "Amenities", "Price"],
        "analysis_context": "property presentation, trust signals, location clarity, price visibility",
        "market_trends": "High-quality property images, clear pricing, location prominence, amenity highlights, trust badges (RERA), professional photography, virtual tours indication"
    },
    "jewellery": {
        "name": "Jewellery",
        "category_check": "jewellery, jewelry, gems, diamonds, gold, silver, necklaces, rings",
        "screening_focus": ["Jewellery Type", "Product Category", "Carat/Purity", "Store/Brand"],
        "analysis_context": "product presentation, luxury appeal, trust signals, price clarity",
        "market_trends": "Elegant backgrounds, close-up product shots, metallic color schemes, certification badges, premium fonts, minimalist layouts, price or 'Contact for price' clarity"
    },
    "automobile": {
        "name": "Automobile",
        "category_check": "automobile, cars, vehicles, bikes, motorcycles, automotive brands",
        "screening_focus": ["Brand/Model", "Vehicle Type", "Fuel Type", "Features"],
        "analysis_context": "vehicle presentation, feature highlighting, brand trust, pricing",
        "market_trends": "Dynamic vehicle angles, brand logo prominence, feature callouts, bold typography, modern color schemes, spec highlights, financing options visibility"
    },
    "ecommerce": {
        "name": "E-commerce",
        "category_check": "e-commerce, online shopping, product listings, marketplace, buy now",
        "screening_focus": ["Product Name", "Price/Discount", "Call-to-Action", "Shipping Info"],
        "analysis_context": "product appeal, pricing strategy, urgency creation, trust signals",
        "market_trends": "Clear product images, discount badges, urgent CTAs, free shipping callouts, star ratings, limited-time offers, mobile-optimized layouts"
    },
    "healthcare": {
        "name": "Healthcare",
        "category_check": "healthcare, medical services, hospitals, clinics, doctors, medicines",
        "screening_focus": ["Service Type", "Credentials", "Contact Info", "Location"],
        "analysis_context": "professional presentation, credentials visibility, service clarity",
        "market_trends": "Professional imagery, doctor credentials, certification displays, calming color schemes (blues/greens), clear contact info, appointment CTAs"
    }
}

ocr_reader = None

# --- HELPER FUNCTIONS ---

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_file_size(file):
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    return file_size <= 16 * 1024 * 1024

def get_image_resolution(image_path):
    try:
        with Image.open(image_path) as img:
            return f"{img.width} x {img.height} pixels"
    except Exception as e:
        return "Unknown"

def get_text_from_image(image_path):
    if ocr_reader is None: 
        return "OCR not available"
    try:
        results = ocr_reader.readtext(image_path, detail=0, paragraph=True)
        full_text = " ".join(results)
        return full_text if full_text else "No text extracted"
    except Exception as e: 
        return "No text extracted"

def encode_image_to_base64(image_path):
    try:
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type or not mime_type.startswith('image'): 
            raise ValueError("Invalid image")
        with open(image_path, "rb") as image_file: 
            encoded = base64.b64encode(image_file.read()).decode('utf-8')
        return f"data:{mime_type};base64,{encoded}"
    except Exception as e: 
        print(f"Error encoding image: {e}")
        return None

def cleanup_uploaded_files():
    """Clean up old files only when explicitly called (on GET request for new analysis)"""
    try:
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(filepath):
                os.unlink(filepath)
        print("✅ Cleaned up uploads")
    except Exception as e:
        print(f"Cleanup error: {e}")

# --- AI FUNCTIONS ---

def check_image_category(image_path, sector_key):
    """LENIENT category check"""
    print(f"🔍 Checking if image is '{SECTOR_CONFIG[sector_key]['name']}'...")
    base64_image = encode_image_to_base64(image_path)
    if not base64_image: 
        return True
    
    category_description = SECTOR_CONFIG[sector_key]['category_check']
    sector_name = SECTOR_CONFIG[sector_key]['name']
    
    prompt = f"Is this image related to {sector_name} advertising? Look for: {category_description}. Answer only 'Yes' or 'No'."
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": f"Be lenient. If image has ANY connection to {sector_name}, say Yes."},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": base64_image}},
                ]}
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct", 
            max_tokens=15, 
            temperature=0.0
        )
        response = chat_completion.choices[0].message.content.strip().lower()
        print(f"   Guardrail response: '{response}'")
        
        if "yes" in response or "correct" in response:
            return True
        elif "no" in response or "false" in response:
            return False
        else:
            return True
            
    except Exception as e:
        print(f"   Guardrail error: {e}")
        return True

def get_screening_score(image_path, resolution, sector_key):
    print("📋 Getting Screening Score...")
    base64_image = encode_image_to_base64(image_path)
    if not base64_image:
        return "<p>Screening analysis unavailable</p>"

    sector_name = SECTOR_CONFIG[sector_key]['name']
    focus_areas = SECTOR_CONFIG[sector_key]['screening_focus']
    focus_lines = "\n".join([f"{f}: [Analysis]" for f in focus_areas])

    prompt = f"""Look at this {sector_name} advertisement image VERY carefully. Read every text visible in the image.

Answer each field based on what you can literally SEE and READ in the image:
Image Resolution: {resolution}
Headline Found: [Yes/No]
CTA Found: [Yes/No - look for Book Now, Contact Us, Call Today etc]
Contact Details Found: [Yes/No - look for phone numbers, email, website]
Price Found: [Yes/No - look for any number with Cr, Lakh, Rs, rupee symbol]
Social Media Mentioned: [Yes/No]
{focus_lines}

READ THE IMAGE TEXT CAREFULLY before answering. Do not say No if you can see it."""

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": f"You are a {sector_name} ad screening expert. Analyze the image and respond in Key-Value format only. No extra text."},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": base64_image}},
                ]}
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            max_tokens=500,
            temperature=0.1
        )
        response_text = chat_completion.choices[0].message.content
        lines = [line.strip() for line in response_text.strip().split('\n') if line.strip()]

        html_output = ""
        for line in lines:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip() + ':'
                value = parts[1].strip()
                value_class = 'yes' if value.lower() == 'yes' else ('no' if value.lower() == 'no' else 'other')
                html_output += f"<div class='screening-item'><span class='key'>{key}</span><span class='value {value_class}'>{value}</span></div>\n"

        return html_output if html_output else "<p>Screening complete</p>"
    except Exception as e:
        print(f"   Screening error: {e}")
        return "<p>Screening analysis unavailable</p>"
        response_text = chat_completion.choices[0].message.content
        lines = [line.strip() for line in response_text.strip().split('\n') if line.strip()]

        html_output = ""
        for line in lines:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip() + ':'
                value = parts[1].strip()
                value_class = 'yes' if value.lower() == 'yes' else ('no' if value.lower() == 'no' else 'other')
                html_output += f"<div class='screening-item'><span class='key'>{key}</span><span class='value {value_class}'>{value}</span></div>\n"
        
        return html_output if html_output else "<p>Screening complete</p>"
    except Exception as e:
        print(f"   Screening error: {e}")
        return "<p>Screening analysis unavailable</p>"

def get_main_scores(image_path, sector_key, ad_text):
    print("🎯 AI Call 1: Getting Scores...")
    base64_image = encode_image_to_base64(image_path)
    if not base64_image: 
        return None

    sector_name = SECTOR_CONFIG[sector_key]['name']
    analysis_context = SECTOR_CONFIG[sector_key]['analysis_context']

    prompt = f"""You are AdScore AI analyzing a {sector_name} advertisement.

CRITICAL INSTRUCTION: Look at the image carefully and describe what you see.

Focus on: {analysis_context}

Format EXACTLY like this:

Overall AdScore: [number]/100
Summary: [one sentence about THIS SPECIFIC ad based on what you see]

---[CRITERIA SCORES]---
1. Visual Clarity & Layout Score: [number]/10
2. Color Combination Score: [number]/10
3. Text Placement & Readability Score: [number]/10
4. Logo Placement Score: [number]/10
5. Image Quality & Relevance Score: [number]/10
6. Overall Impression Score: [number]/10

Extracted Text: "{ad_text}"
"""

    for attempt in range(3):
        print(f"   Attempt {attempt + 1}/3")
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a professional ad analyst. Analyze the image carefully and provide specific observations."},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": base64_image}},
                    ]}
                ],
                model="meta-llama/llama-4-scout-17b-16e-instruct", 
                max_tokens=1500, 
                temperature=0.5
            )
            raw_text = chat_completion.choices[0].message.content
            print(f"   Response received: {len(raw_text)} chars")

            overall_match = re.search(r"Overall AdScore:\s*(\d+)/100", raw_text, re.IGNORECASE)
            overall_score = int(overall_match.group(1)) if overall_match else None

            summary_match = re.search(r"Summary:\s*(.*?)(?:\n|---)", raw_text, re.IGNORECASE | re.DOTALL)
            summary = summary_match.group(1).strip() if summary_match else "Analysis complete."

            scores_matches = re.findall(r"\d+\.\s+([^:]+):\s*(\d+)/10", raw_text)
            
            if scores_matches and len(scores_matches) >= 4:
                criteria_list = []
                for name, score in scores_matches:
                    criteria_list.append({
                        "name": name.strip(),
                        "score": int(score),
                        "max_score": 10
                    })
                
                if not overall_score:
                    avg_score = sum(c['score'] for c in criteria_list) / len(criteria_list)
                    overall_score = int((avg_score / 10) * 100)
                
                print(f"   ✅ SUCCESS with {len(criteria_list)} criteria")
                return {
                    "overall_score": overall_score,
                    "summary": summary,
                    "criteria": criteria_list
                }
            else:
                print(f"   ⚠️ Only {len(scores_matches)} criteria found")
                
        except Exception as e:
            print(f"   ❌ Attempt {attempt + 1} failed: {e}")
        
        time.sleep(1)

    print("❌ All attempts failed")
    return None

def get_detailed_analysis(image_path, sector_key, ad_text, criteria_list):
    print("💡 AI Call 2: Getting IMAGE-SPECIFIC Detailed Analysis...")
    base64_image = encode_image_to_base64(image_path)
    if not base64_image: 
        return {"criteria_analysis": []}

    sector_name = SECTOR_CONFIG[sector_key]['name']
    analysis_context = SECTOR_CONFIG[sector_key]['analysis_context']
    market_trends = SECTOR_CONFIG[sector_key]['market_trends']
    criteria_names = [c['name'] for c in criteria_list]
    criteria_text = "\n".join([f"{i+1}. {name}" for i, name in enumerate(criteria_names)])

    prompt = f"""You are a professional {sector_name} advertisement analyst with expertise in visual design, color theory, typography, and {sector_name} marketing.

🔥 CRITICAL MISSION - READ CAREFULLY:
You MUST analyze THIS SPECIFIC IMAGE and provide UNIQUE, IMAGE-SPECIFIC advice for EACH criterion.

SECTOR: {sector_name}
CONTEXT: {analysis_context}
CURRENT MARKET TRENDS: {market_trends}

📋 CRITERIA TO ANALYZE:
{criteria_text}

🎯 YOUR ANALYSIS APPROACH:

STEP 1: VISUAL EXAMINATION
- Look at the actual image
- Identify colors (hex codes like #FF5733)
- Note text positions (top-left, center, bottom)
- Measure approximate sizes (small 12pt, medium 24pt, large 48pt)
- Observe layout (crowded/spacious/balanced)
- Locate elements (logo position, CTA placement)

STEP 2: FOR EACH CRITERION - PROVIDE:

**Criteria: [Exact Name]**
**Evaluation: Success or Fail**
**Reason: [2-3 sentences describing what you SEE in this image that makes it succeed/fail. Reference actual colors, positions, sizes, elements visible in the image]**
**Advice: [Specific fix 1 based on what you see] | [Specific fix 2 for this image] | [Specific fix 3 referencing market trends]**

🚨 CRITICAL RULES:
1. Each criterion MUST have DIFFERENT advice (Color advice ≠ Layout advice ≠ Text advice)
2. Reference ACTUAL visual elements you see
3. Use measurements: "Move from X to Y", "Change #FF0000 to #0066CC", "Increase from 12pt to 24pt"
4. Apply {sector_name} market trends
5. Use | separator between advice points
6. Make advice ACTIONABLE and SPECIFIC to this image

EXAMPLE OF EXCELLENT ADVICE:
**Criteria: Color Combination Score**
**Evaluation: Fail**
**Reason: The bright red background (#FF0000) clashes with the yellow text (#FFFF00), creating poor readability and appearing unprofessional for real estate marketing.**
**Advice: Replace red background with professional navy blue (#1E3A8A) to convey trust | Change yellow text to white (#FFFFFF) for maximum contrast | Add a subtle gradient overlay to create depth and premium feel**

EXAMPLE OF EXCELLENT ADVICE:
**Criteria: Text Placement & Readability Score**
**Evaluation: Success**
**Reason: The headline is positioned in the top-third area with 36pt font, making it immediately visible. However, the contact details at bottom are only 8pt, too small for mobile viewing.**
**Advice: Maintain headline position but increase font to 42pt for stronger impact | Move contact details from bottom-right to top-left corner in 14pt size | Add a semi-transparent background box behind contact info for better separation**

NOW ANALYZE THIS {sector_name} IMAGE:
Extracted Text: "{ad_text}"

Provide your analysis for ALL criteria with UNIQUE, IMAGE-SPECIFIC advice:"""

    for attempt in range(3):
        print(f"   Attempt {attempt + 1}/3")
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": f"You are an expert {sector_name} ad analyst. You MUST look at the image and give SPECIFIC advice for each criterion based on what you actually SEE. Each criterion needs DIFFERENT advice. Use | separator for bullet points."},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": base64_image}},
                    ]}
                ],
                model="meta-llama/llama-4-scout-17b-16e-instruct", 
                max_tokens=4096,
                temperature=0.7
            )
            raw_response = chat_completion.choices[0].message.content
            print(f"   Detailed analysis response length: {len(raw_response)}")
            
            criteria_analysis = []
            blocks = re.split(r'(?=\*\*Criteria:|\nCriteria:)', raw_response)
            
            for block in blocks:
                if not block.strip():
                    continue
                    
                criteria_match = re.search(r'\*?\*?Criteria:\s*(.+?)(?:\n|\*\*)', block, re.IGNORECASE)
                eval_match = re.search(r'\*?\*?Evaluation:\s*(Success|Fail)', block, re.IGNORECASE)
                reason_match = re.search(r'\*?\*?Reason:\s*(.+?)(?:\n\*?\*?Advice:|\*\*Advice)', block, re.IGNORECASE | re.DOTALL)
                advice_match = re.search(r'\*?\*?Advice:\s*(.+?)(?:\n\n|\*\*Criteria:|\nCriteria:|---|\Z)', block, re.IGNORECASE | re.DOTALL)
                
                if criteria_match:
                    criteria_name = criteria_match.group(1).strip().replace('**', '')
                    evaluation = eval_match.group(1) if eval_match else "Success"
                    reason = reason_match.group(1).strip() if reason_match else "Analysis based on image examination"
                    
                    advice_text = advice_match.group(1).strip() if advice_match else ""
                    
                    # Enhanced parsing: split by | and clean
                    advice_points = []
                    if '|' in advice_text:
                        advice_points = [p.strip() for p in advice_text.split('|') if p.strip()]
                    elif '\n-' in advice_text or '\n•' in advice_text:
                        advice_points = [p.strip().lstrip('-•').strip() for p in advice_text.split('\n') if p.strip() and len(p.strip()) > 1 and p.strip()[0] in ['-', '•']]
                    else:
                        if ';' in advice_text:
                            advice_points = [p.strip() for p in advice_text.split(';') if p.strip()]
                        elif '. ' in advice_text and len(advice_text) > 100:
                            advice_points = [p.strip() + '.' for p in advice_text.split('. ') if p.strip() and len(p.strip()) > 10]
                        else:
                            advice_points = [advice_text] if advice_text else []
                    
                    # Clean up markdown and formatting
                    advice_points = [p.replace('**', '').strip() for p in advice_points]
                    
                    # Ensure we have at least one advice point
                    if not advice_points:
                        advice_points = [f'Review {criteria_name.lower()} based on {sector_name} industry standards', f'Analyze current {criteria_name.lower()} against market trends', f'Test {criteria_name.lower()} improvements with target audience']
                    
                    # Limit to 3 points
                    advice_points = advice_points[:3]
                    
                    criteria_analysis.append({
                        "criteria": criteria_name,
                        "evaluation": evaluation,
                        "reason": reason,
                        "advice_points": advice_points
                    })
                    
                    print(f"   ✓ Parsed {criteria_name}: {len(advice_points)} advice points")
            
            if len(criteria_analysis) >= len(criteria_list) - 1:
                print(f"   ✅ SUCCESS with {len(criteria_analysis)} analyzed")
                return {"criteria_analysis": criteria_analysis}
            else:
                print(f"   ⚠️ Only {len(criteria_analysis)} criteria analyzed, retrying...")
                
        except Exception as e:
            print(f"   ❌ Attempt {attempt + 1} failed: {e}")
            traceback.print_exc()
            time.sleep(1)

    print("⚠️ Using intelligent fallback analysis")
    fallback = []
    for criterion in criteria_list:
        fallback.append({
            "criteria": criterion['name'],
            "evaluation": "Success" if criterion['score'] >= 6 else "Fail",
            "reason": f"Scored {criterion['score']}/10 in initial analysis based on visual assessment.",
            "advice_points": [
                f"Review current {criterion['name'].lower()} implementation against {sector_name} standards",
                f"Consider {sector_name} market trends: {market_trends[:100]}...",
                f"Test {criterion['name'].lower()} improvements with target audience feedback"
            ]
        })
    return {"criteria_analysis": fallback}

def get_platform_analysis(image_path, sector_key, ad_text):
    print("🌐 AI Call 3: Getting IMAGE-SPECIFIC Platform Analysis...")
    base64_image = encode_image_to_base64(image_path)
    if not base64_image: 
        return {"platform_analysis": []}

    sector_name = SECTOR_CONFIG[sector_key]['name']
    market_trends = SECTOR_CONFIG[sector_key]['market_trends']

    prompt = f"""Analyze THIS SPECIFIC {sector_name} advertisement image for platform performance.

🔥 CRITICAL INSTRUCTIONS:
1. LOOK at the actual image (colors, layout, text size, aspect ratio)
2. For EACH platform, explain WHY this specific image would/wouldn't work
3. Reference ACTUAL visual elements you see
4. Consider platform-specific requirements
5. Apply {sector_name} market trends

SECTOR TRENDS: {market_trends}

PLATFORMS TO ANALYZE:
1. Facebook Post (1200x630, mobile-first, blue interface)
2. Instagram Post (1080x1080 square, visual-heavy, young audience)
3. YouTube Thumbnail (1280x720, must grab attention in 2 seconds)
4. Twitter Post (1200x675, fast scrolling, text-heavy users)
5. Google Display Ad (varies, professional context, quick glance)

📋 FORMAT FOR EACH PLATFORM:

**Platform: [Name]**
**Score: [0-10]**
**Rationale: [3-4 sentences explaining WHY this score based on what you SEE in this image. Reference specific elements: colors, text size, layout, aspect ratio, visual hierarchy that would work well or poorly on THIS platform for THIS sector]**

🎯 WHAT MAKES EXCELLENT RATIONALE:

GOOD EXAMPLE:
**Platform: Facebook Post**
**Score: 8/10**
**Rationale: The 16:9 aspect ratio of this ad fits Facebook's feed perfectly. The bright blue background (#0066CC) contrasts well against Facebook's interface, making the ad stand out. The 24pt headline is easily readable on mobile devices, which is critical since 98% of Facebook users access via mobile. However, the contact details at the bottom are only 10pt - these should be increased to 14pt minimum for mobile readability. For real estate, adding a RERA number badge would increase trust on this platform.**

BAD EXAMPLE (TOO GENERIC):
**Platform: Facebook Post**
**Score: 7/10**
**Rationale: Good for Facebook. The ad works well on this platform. Could be improved.**

🚨 CRITICAL RULES:
1. Reference ACTUAL colors, sizes, positions you see in the image
2. Mention aspect ratio and how it fits the platform
3. Consider mobile vs desktop (most traffic is mobile)
4. Apply {sector_name} best practices for each platform
5. Explain what would need to change for better performance
6. Each platform needs DIFFERENT rationale (Instagram ≠ Facebook ≠ YouTube)

Extracted Text: "{ad_text}"

NOW ANALYZE THIS {sector_name} IMAGE FOR ALL 5 PLATFORMS WITH DETAILED RATIONALE:"""

    for attempt in range(3):
        print(f"   Attempt {attempt + 1}/3")
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": f"You are a platform-specific ad analyst for {sector_name}. Give detailed, image-specific rationale for each platform based on what you SEE. Each platform needs DIFFERENT analysis."},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": base64_image}},
                    ]}
                ],
                model="meta-llama/llama-4-scout-17b-16e-instruct", 
                max_tokens=3072, 
                temperature=0.6
            )
            raw_response = chat_completion.choices[0].message.content
            
            platform_analysis = []
            blocks = re.split(r'(?=\*\*Platform:|\nPlatform:)', raw_response)
            
            for block in blocks:
                if not block.strip():
                    continue
                    
                platform_match = re.search(r'\*?\*?Platform:\s*(.+?)(?:\n|\*\*)', block, re.IGNORECASE)
                score_match = re.search(r'\*?\*?Score:\s*(\d+)', block, re.IGNORECASE)
                rationale_match = re.search(r'\*?\*?Rationale:\s*(.+?)(?:\n\n|---|\*\*Platform:|\nPlatform:|\Z)', block, re.IGNORECASE | re.DOTALL)
                
                if platform_match and score_match:
                    platform_name = platform_match.group(1).strip().replace('**', '')
                    score = int(score_match.group(1))
                    rationale = rationale_match.group(1).strip().replace('**', '') if rationale_match else f"Analysis pending for {platform_name}"
                    
                    # Clean up rationale
                    rationale = ' '.join(rationale.split())  # Remove extra whitespace
                    
                    platform_analysis.append({
                        "platform": platform_name,
                        "score": min(score, 10),
                        "rationale": rationale
                    })
                    
                    print(f"   ✓ Parsed {platform_name}: {score}/10")
            
            if len(platform_analysis) >= 4:
                print(f"   ✅ SUCCESS with {len(platform_analysis)} platforms")
                return {"platform_analysis": platform_analysis}
            else:
                print(f"   ⚠️ Only {len(platform_analysis)} platforms found, retrying...")
                
        except Exception as e:
            print(f"   ❌ Attempt {attempt + 1} failed: {e}")
            time.sleep(1)

    print("⚠️ Using sector-aware fallback platforms")
    fallback = [
        {"platform": "Facebook Post", "score": 7, "rationale": f"Standard effectiveness for {sector_name} advertising with good reach potential among target audiences. Mobile optimization recommended."},
        {"platform": "Instagram Post", "score": 8, "rationale": f"Strong visual platform suitable for {sector_name} marketing. High engagement rates with proper hashtag strategy and visual appeal."},
        {"platform": "YouTube Thumbnail", "score": 6, "rationale": f"Moderate effectiveness for {sector_name} video content. Requires high-contrast elements and clear messaging to capture attention."},
        {"platform": "Twitter Post", "score": 6, "rationale": f"Quick messaging capability for {sector_name} announcements. Best with concise copy and trending hashtags for visibility."},
        {"platform": "Google Display Ad", "score": 7, "rationale": f"Compatible with {sector_name} search targeting. Professional presentation matches user intent in search context."}
    ]
    return {"platform_analysis": fallback}

# --- ROUTES ---

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/sectors', methods=['GET'])
def get_sectors():
    sectors = []
    for key, config in SECTOR_CONFIG.items():
        sectors.append({"key": key, "name": config["name"]})
    return jsonify({"sectors": sectors})

# HOMEPAGE ROUTE
@app.route('/')
def index():
    return render_template('index.html')

# FREE TRIAL ROUTE - HANDLES UPLOAD AND RESULTS
@app.route('/free-trial', methods=['GET', 'POST'])
def free_trial():
    if request.method == 'GET':
        cleanup_uploaded_files()
        return render_template('free-trial.html', sectors=SECTOR_CONFIG)
    
    error_message = None

    try:
        file = request.files.get('file')
        sector_key = request.form.get('category')

        if not file or file.filename == '':
            error_message = "Please select a file to upload."
            return render_template('free-trial.html', error=error_message, sectors=SECTOR_CONFIG)

        if sector_key not in SECTOR_CONFIG:
            error_message = "Invalid sector selected."
            return render_template('free-trial.html', error=error_message, sectors=SECTOR_CONFIG)

        if file and allowed_file(file.filename):
            if not check_file_size(file):
                error_message = "File too large. Maximum 16MB."
                return render_template('free-trial.html', error=error_message, sectors=SECTOR_CONFIG)
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            print(f"📁 File saved: {filepath}")

            is_correct_category = check_image_category(filepath, sector_key)
            
            if not is_correct_category:
                sector_name = SECTOR_CONFIG[sector_key]['name']
                error_message = f"This doesn't appear to be a {sector_name} ad."
                try:
                    os.unlink(filepath)
                except:
                    pass
                return render_template('free-trial.html', error=error_message, sectors=SECTOR_CONFIG)

            print("✅ Guardrail passed")
            
            resolution = get_image_resolution(filepath)
            ad_text = get_text_from_image(filepath)

            screening_results_html = get_screening_score(filepath, resolution, sector_key)
            main_analysis = get_main_scores(filepath, sector_key, ad_text)
            
            if not main_analysis:
                error_message = "AI analysis failed. Please try a clearer image."
                try:
                    os.unlink(filepath)
                except:
                    pass
                return render_template('free-trial.html', error=error_message, sectors=SECTOR_CONFIG)
            
            detailed_analysis = get_detailed_analysis(filepath, sector_key, ad_text, main_analysis['criteria'])
            platform_analysis = get_platform_analysis(filepath, sector_key, ad_text)

            analysis_results = {
                "uploaded_file": filename,
                "sector_name": SECTOR_CONFIG[sector_key]['name'],
                "overall_score": main_analysis['overall_score'],
                "summary": main_analysis['summary'],
                "criteria": main_analysis['criteria'],
                "criteria_analysis": detailed_analysis.get('criteria_analysis', []),
                "platform_analysis": platform_analysis.get('platform_analysis', []),
                "screening_html": screening_results_html
            }

            print("✅ Analysis complete!")
            print(f"📷 Image preserved: {filepath}")
            
            return render_template('free-trial.html', results=analysis_results, sectors=SECTOR_CONFIG)
        else:
            error_message = "Invalid file type. Use: png, jpg, jpeg, gif"

    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        error_message = f"Unexpected error: {str(e)}"

    return render_template('free-trial.html', error=error_message, sectors=SECTOR_CONFIG)

if __name__ == '__main__':
    print("\n🚀 Starting AdScore - Dynamic Ad Analysis System")
    print("📊 All 5 sectors available: Real Estate, Jewellery, Automobile, E-commerce, Healthcare")
    print("✨ Enhanced Image-specific AI analysis with sector-aware market trends\n")
    app.run(debug=True)