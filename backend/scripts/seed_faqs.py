"""Script to seed FAQs with embeddings into MongoDB."""
import sys
import os
import time
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.faq import FAQ
from app.services.embedding_service import generate_embedding
from app.db.mongodb import create_indexes
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# FAQs for VibeThreads - Gen Z Clothing Brand
# Specializing in oversized t-shirts, streetwear, and accessories
SAMPLE_FAQS = [
    {
        "category": "Shipping",
        "question": "What is your shipping policy?",
        "answer": "We offer free standard shipping on orders over $50. Standard shipping takes 5-7 business days. Express shipping (2-3 business days) is available for an additional $10. International shipping is available to select countries with rates calculated at checkout."
    },
    {
        "category": "Shipping",
        "question": "Do you ship to the USA?",
        "answer": "Yes, we ship to all 50 US states. Standard shipping takes 5-7 business days, and express shipping (2-3 business days) is available for an additional $10."
    },
    {
        "category": "Shipping",
        "question": "How long does shipping take?",
        "answer": "Standard shipping takes 5-7 business days. Express shipping takes 2-3 business days. Processing time is 1-2 business days before your order ships."
    },
    {
        "category": "Shipping",
        "question": "Do you offer international shipping?",
        "answer": "Yes! We ship worldwide to over 50 countries. International shipping rates and delivery times vary by location. Check out our shipping calculator at checkout for exact rates and estimated delivery times."
    },
    {
        "category": "Returns",
        "question": "What is your return policy?",
        "answer": "We offer a 30-day return policy. Items must be unused, unwashed, in original packaging, and with tags attached. Returns are free for orders over $50. To initiate a return, contact our support team with your order number or use the return portal in your account."
    },
    {
        "category": "Returns",
        "question": "How do I return an item?",
        "answer": "To return an item, contact our support team with your order number or visit your account dashboard. We'll provide you with a return authorization and prepaid shipping label. Items must be returned within 30 days of delivery, unused and in original packaging with tags attached."
    },
    {
        "category": "Returns",
        "question": "What is your refund policy?",
        "answer": "Refunds are processed within 5-7 business days after we receive your returned item. The refund will be issued to the original payment method. Shipping costs are non-refundable unless the return is due to our error or a defective item."
    },
    {
        "category": "Returns",
        "question": "Can I exchange an item for a different size?",
        "answer": "Yes! We offer free exchanges for size issues within 30 days. Contact support with your order number and the size you need. If the new size is in stock, we'll process the exchange. If not, we'll refund and you can reorder."
    },
    {
        "category": "Products",
        "question": "What sizes do your oversized t-shirts come in?",
        "answer": "Our oversized t-shirts come in sizes XS through 3XL. They're designed with a relaxed, boxy fit perfect for that streetwear vibe. Check each product page for specific size charts and measurements. Most styles run true to size for an oversized look."
    },
    {
        "category": "Products",
        "question": "How do I choose the right size for oversized fit?",
        "answer": "For a true oversized look, go one size up from your usual size. For a slightly relaxed fit, stick with your regular size. Check our size guide on each product page for exact measurements. Our oversized tees are designed to be roomy and comfortable."
    },
    {
        "category": "Products",
        "question": "What materials are your t-shirts made from?",
        "answer": "Our t-shirts are made from 100% premium cotton or cotton blends for maximum comfort. We use soft, breathable fabrics that hold up wash after wash. Each product page lists the exact material composition. All items are pre-shrunk to maintain their fit."
    },
    {
        "category": "Products",
        "question": "Do you have accessories?",
        "answer": "Yes! We have a full accessories collection including bucket hats, beanies, socks, tote bags, phone cases, and jewelry. Check out our accessories section for the latest drops. New items drop every week!"
    },
    {
        "category": "Products",
        "question": "Are your products limited edition?",
        "answer": "Many of our designs are limited edition drops that sell out fast! We release new collections monthly. Follow us on social media @vibethreads for drop announcements. Once a style sells out, it may not restock, so grab your favorites while they last!"
    },
    {
        "category": "Products",
        "question": "Do you offer product warranties?",
        "answer": "Yes, all our products come with a 1-year warranty covering defects in materials and workmanship. If you receive a defective item, contact us immediately with photos and your order number for a free replacement or refund."
    },
    {
        "category": "Products",
        "question": "Can I track my order?",
        "answer": "Yes, once your order ships, you'll receive a tracking number via email. You can track your order status in your account dashboard or by clicking the tracking link in the email. We'll also send you updates as your package moves through shipping."
    },
    {
        "category": "Products",
        "question": "Do you offer gift wrapping?",
        "answer": "Yes! We offer gift wrapping for an additional $5. Select the gift wrap option at checkout and add a personalized message. Perfect for birthdays, holidays, or just showing someone you care. Gift receipts are included automatically."
    },
    {
        "category": "Support",
        "question": "What are your support hours?",
        "answer": "Our customer support team is available Monday through Friday, 9 AM to 6 PM EST, and Saturday 10 AM to 4 PM EST. We typically respond to emails and live chat within 24 hours. For urgent issues, use our live chat for faster response times."
    },
    {
        "category": "Support",
        "question": "How can I contact customer support?",
        "answer": "You can reach us via email at support@vibethreads.com, through our live chat widget on the website, or DM us on Instagram @vibethreads. We're available Monday-Friday 9 AM-6 PM EST and Saturday 10 AM-4 PM EST. We're here to help!"
    },
    {
        "category": "Support",
        "question": "Do you have a student discount?",
        "answer": "Yes! Students get 15% off with a valid student email. Sign up for our newsletter to get your student discount code. We also run flash sales and promo codes on our social media @vibethreads - follow us for the latest deals!"
    },
    {
        "category": "Payment",
        "question": "What payment methods do you accept?",
        "answer": "We accept all major credit cards (Visa, Mastercard, American Express, Discover), PayPal, Apple Pay, Google Pay, Shop Pay, and Afterpay for flexible payments. All payments are processed securely through encrypted connections."
    },
    {
        "category": "Payment",
        "question": "Is my payment information secure?",
        "answer": "Yes, we use industry-standard SSL encryption to protect your payment information. We never store your full credit card details on our servers. All payments are processed through secure, PCI-compliant payment gateways. Your data is safe with us!"
    },
    {
        "category": "Payment",
        "question": "Do you offer payment plans?",
        "answer": "Yes! We partner with Afterpay and Klarna to offer flexible payment plans. Split your purchase into 4 interest-free payments. Select Afterpay or Klarna at checkout to see if you qualify. It's super easy and no credit check required!"
    },
    {
        "category": "General",
        "question": "What is VibeThreads?",
        "answer": "VibeThreads is a Gen Z-focused clothing brand specializing in oversized t-shirts, streetwear, and accessories. We're all about self-expression, comfort, and that perfect oversized fit. Our designs are fresh, our vibes are immaculate, and our community is everything."
    },
    {
        "category": "General",
        "question": "Do you have a loyalty program?",
        "answer": "Yes! Join our Vibe Squad loyalty program and earn points with every purchase. Get 1 point per dollar spent, plus bonus points for reviews and referrals. Redeem points for discounts and exclusive early access to new drops. Sign up is free!"
    },
    {
        "category": "General",
        "question": "How do I stay updated on new drops?",
        "answer": "Follow us on Instagram @vibethreads and TikTok @vibethreads for the latest drops, styling tips, and behind-the-scenes content. Sign up for our newsletter to get early access and exclusive discounts. New collections drop monthly!"
    }
]


def seed_faqs():
    """Seed FAQs with embeddings into MongoDB."""
    try:
        logger.info("Creating database indexes...")
        create_indexes()
        
        # Check which embedding service is configured
        from app.services.embedding_service import COHERE_MODEL, COHERE_API_KEY, HF_API_KEY
        if COHERE_API_KEY:
            logger.info(f"Generating embeddings for FAQs using Cohere API (model: {COHERE_MODEL})...")
            logger.info("Note: Using 'search_document' input type for FAQ content")
        elif HF_API_KEY:
            logger.info("Generating embeddings for FAQs using Hugging Face API...")
            logger.info("Note: First request may take 5-10 seconds (model loading)")
        else:
            logger.error("No embedding API key configured!")
            raise Exception("Please set COHERE_API_KEY or HUGGINGFACE_API_KEY in .env file")
        faqs_to_insert = []
        
        for i, faq_data in enumerate(SAMPLE_FAQS, 1):
            try:
                logger.info(f"[{i}/{len(SAMPLE_FAQS)}] Generating embedding for: '{faq_data['question'][:50]}...'")
                # Generate embedding for the question using API
                # Use "search_document" for FAQ content (same model as queries, but optimized for documents)
                question_embedding = generate_embedding(faq_data["question"], input_type="search_document")
                
                faq = FAQ(
                    category=faq_data["category"],
                    question=faq_data["question"],
                    answer=faq_data["answer"],
                    embedding=question_embedding
                )
                faqs_to_insert.append(faq)
                
                # Small delay to respect API rate limits (free tier: ~30 req/min)
                # Wait 2 seconds between requests to stay under limit
                if i < len(SAMPLE_FAQS):
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Failed to generate embedding for FAQ {i}: {e}")
                logger.warning("Continuing with remaining FAQs...")
                # Continue with next FAQ instead of failing completely
                continue
        
        logger.info(f"Inserting {len(faqs_to_insert)} FAQs into database...")
        
        # Clear existing FAQs (optional - comment out if you want to keep existing)
        collection = FAQ.get_collection()
        collection.delete_many({})
        logger.info("Cleared existing FAQs")
        
        # Insert FAQs
        for faq in faqs_to_insert:
            faq.save()
        
        logger.info(f"Successfully seeded {len(faqs_to_insert)} FAQs with embeddings!")
        
    except Exception as e:
        logger.error(f"Error seeding FAQs: {e}")
        raise


if __name__ == "__main__":
    seed_faqs()

