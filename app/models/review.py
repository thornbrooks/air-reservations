from firebase_admin import firestore as fs

class Review:
    COLLECTION = 'reviews'

    @staticmethod
    def create(user_id, listing_id, listing_type, data):
        from app.firebase_config import db
        if not db: return None
        ref = db.collection(Review.COLLECTION).document()
        ref.set({
            'id': ref.id,
            'userId': user_id,
            'listingId': listing_id,
            'listingType': listing_type,
            'rating': int(data.get('rating', 5)),
            'comment': data.get('comment', '').strip(),
            'reviewerName': data.get('reviewer_name', 'Guest'),
            'created_at': fs.SERVER_TIMESTAMP,
        })
        return ref.id

    @staticmethod
    def get_by_listing(listing_id):
        from app.firebase_config import db
        if not db: return []
        docs = db.collection(Review.COLLECTION).where(
            filter=fs.FieldFilter('listingId', '==', listing_id)
        ).stream()
        return sorted([doc.to_dict() for doc in docs],
                      key=lambda x: x.get('created_at') or 0, reverse=True)

    @staticmethod
    def has_reviewed(user_id, listing_id):
        from app.firebase_config import db
        if not db: return False
        docs = db.collection(Review.COLLECTION)\
            .where(filter=fs.FieldFilter('userId', '==', user_id))\
            .where(filter=fs.FieldFilter('listingId', '==', listing_id))\
            .stream()
        return any(True for _ in docs)
