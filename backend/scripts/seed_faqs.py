"""Script to seed FAQs with embeddings into MongoDB."""
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.faq import FAQ
from app.services.embedding_service import generate_embedding
from app.db.mongodb import create_indexes
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Sample FAQs for a fictional e-commerce store
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
        "category": "Returns",
        "question": "What is your return policy?",
        "answer": "We offer a 30-day return policy. Items must be unused, in original packaging, and with tags attached. Returns are free for orders over $50. To initiate a return, please contact our support team with your order number."
    },
    {
        "category": "Returns",
        "question": "How do I return an item?",
        "answer": "To return an item, please contact our support team with your order number. We'll provide you with a return authorization and shipping label. Items must be returned within 30 days of delivery, unused and in original packaging."
    },
    {
        "category": "Returns",
        "question": "What is your refund policy?",
        "answer": "Refunds are processed within 5-7 business days after we receive your returned item. The refund will be issued to the original payment method. Shipping costs are non-refundable unless the return is due to our error."
    },
    {
        "category": "Support",
        "question": "What are your support hours?",
        "answer": "Our customer support team is available Monday through Friday, 9 AM to 6 PM EST. You can reach us via email, live chat, or phone. We typically respond to emails within 24 hours."
    },
    {
        "category": "Support",
        "question": "How can I contact customer support?",
        "answer": "You can contact our customer support team via email at support@example.com, through our live chat widget on the website, or by calling 1-800-EXAMPLE. We're available Monday through Friday, 9 AM to 6 PM EST."
    },
    {
        "category": "Products",
        "question": "Do you offer product warranties?",
        "answer": "Yes, all our products come with a 1-year manufacturer's warranty covering defects in materials and workmanship. Extended warranties are available for select items at checkout."
    },
    {
        "category": "Products",
        "question": "Can I track my order?",
        "answer": "Yes, once your order ships, you'll receive a tracking number via email. You can track your order status in your account dashboard or by clicking the tracking link in the email."
    },
    {
        "category": "Payment",
        "question": "What payment methods do you accept?",
        "answer": "We accept all major credit cards (Visa, Mastercard, American Express), PayPal, Apple Pay, and Google Pay. All payments are processed securely through encrypted connections."
    },
    {
        "category": "Payment",
        "question": "Is my payment information secure?",
        "answer": "Yes, we use industry-standard SSL encryption to protect your payment information. We never store your full credit card details on our servers. All payments are processed through secure, PCI-compliant payment gateways."
    }
]


def seed_faqs():
    """Seed FAQs with embeddings into MongoDB."""
    try:
        logger.info("Creating database indexes...")
        create_indexes()
        
        logger.info("Generating embeddings for FAQs...")
        faqs_to_insert = []
        
        for faq_data in SAMPLE_FAQS:
            # Generate embedding for the question
            question_embedding = generate_embedding(faq_data["question"])
            
            faq = FAQ(
                category=faq_data["category"],
                question=faq_data["question"],
                answer=faq_data["answer"],
                embedding=question_embedding
            )
            faqs_to_insert.append(faq)
        
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

