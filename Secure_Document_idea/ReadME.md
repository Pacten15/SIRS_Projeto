Restaurants & Tourism: BombAppetit

BombAppetit is a web application tailored to enhance the dining experience. It simplifies restaurant reservations with an intuitive interface. Users can explore a curated list of local restaurants based on their location, making it easy to find the perfect dining spot. BombAppetit facilitates table reservations for any group size.
The system integrates with a discount card service, allowing patrons to redeem their accumulated points for attractive booking discounts. BombAppetit revolutionizes dining convenience, connecting users with delightful culinary experiences.

The core data handled by the application is exemplified next:

{
  "restaurantInfo": {
    "owner": "Maria Silva",
    "restaurant": "Dona Maria",
    "address": "Rua da Glória, 22, Lisboa",
    "genre": ["Portuguese", "Traditional"],
    "menu": [
      {
        "itemName": "House Steak",
        "category": "Meat",
        "description": "A succulent sirloin grilled steak.",
        "price": 24.99,
        "currency": "EUR"
      },
      {
        "itemName": "Sardines",
        "category": "Fish",
        "description": "A Portuguese staple, accompanied by potatoes and salad.",
        "price": 21.99,
        "currency": "EUR"
      },
      {
        "itemName": "Mushroom Risotto",
        "category": "Vegetarian",
        "description": "Creamy Arborio rice cooked with assorted mushrooms and Parmesan cheese.",
        "price": 16.99,
        "currency": "EUR"
      }
    ],
    "mealVoucher": {
      "code": "VOUCHER123",
      "description": "Redeem this code for a 20% discount in the meal. Drinks not included."
    }
  }
}

Protection Needs

The protected document must ensure the authenticity of the restaurant data. If a voucher exists, it should be confidential so that only the user should be able to access it.
You can assume that the user and the service share their respective public keys.