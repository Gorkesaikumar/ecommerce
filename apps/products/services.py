from decimal import Decimal
from .models import Product, DimensionConfig

class PricingService:
    @staticmethod
    def calculate_price(product_id: str, length: float, breadth: float, height: float) -> dict:
        """
        Calculates the price of a product based on its dimensions.
        Priority:
        1. Exact match in ProductDimension
        2. Range match in DimensionConfig
        3. Base Price (fallback)
        """
        product = Product.objects.get(id=product_id)

        # 1. Check for Exact ProductDimension Match
        try:
            from .models import ProductDimension
            dim = ProductDimension.objects.get(
                product=product,
                length=length,
                breadth=breadth,
                height=height
            )
            return {
                "final_price": dim.price,
                "base_price": dim.price, # Treat as base
                "multiplier": Decimal("1.0"),
                "add_on": Decimal("0.0"),
                "config_id": None,
                "dimension_id": dim.id
            }
        except (ProductDimension.DoesNotExist, ImportError):
            pass
        
        # 2. Check Range Config (Legacy/Fallback)
        if product.dimension_configs.exists():
            configs = product.dimension_configs.all()
            matching_config = None

            for config in configs:
                if (config.min_length <= length <= config.max_length and
                    config.min_breadth <= breadth <= config.max_breadth and
                    config.min_height <= height <= config.max_height):
                    matching_config = config
                    break
            
            if not matching_config:
                raise ValueError(f"Dimensions {length}x{breadth}x{height} are not available for this product.")

            # Price Calculation Logic
            base = product.base_price
            multiplier = matching_config.price_multiplier
            add_on = matching_config.price_add_on
            
            final_price = (base * multiplier) + add_on
            
            return {
                "final_price": final_price.quantize(Decimal("0.01")),
                "base_price": base,
                "multiplier": multiplier,
                "add_on": add_on,
                "config_id": matching_config.id
            }

        # 3. Fallback to Base Price if no configs exist
        return {
            "final_price": product.base_price,
            "base_price": product.base_price,
            "multiplier": Decimal("1.0"),
            "add_on": Decimal("0.0"),
            "config_id": None
        }
