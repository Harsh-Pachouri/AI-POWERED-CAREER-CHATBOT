import boto3
import traceback
import uuid
from boto3.dynamodb.conditions import Key, Attr

class DBManager:
    def __init__(self, table_name):
        try:
            self.dynamodb = boto3.resource("dynamodb")
            self.table = self.dynamodb.Table(table_name)
            print(f"Successfully initialized DBManager with table: {table_name}")
            
            # Verify table access and get total item count
            response = self.table.scan(Select="COUNT")
            total_items = response.get("Count", 0)
            print(f"Table access verified. Total items count: {total_items}")
        except Exception as e:
            print(f"Error initializing DBManager: {e}")
            traceback.print_exc()
            raise

    def delete_all_entries(self):
        """
        Delete all entries in the table.
        """
        try:
            print("Deleting all entries...")
            response = self.table.scan()
            items = response.get("Items", [])
            
            for item in items:
                resource_id = item["resource_id"]
                category = item["category"]
                self.table.delete_item(Key={"resource_id": resource_id, "category": category})
                print(f"Deleted item with resource_id: {resource_id} and category: {category}")
            
            print("All entries deleted.")
            return True
        except Exception as e:
            print(f"Error deleting entries: {e}")
            traceback.print_exc()
            return False

    def delete_resource(self, resource_id, category):
        """
        Delete a specific resource by resource_id and category.
        """
        try:
            print(f"Deleting resource with resource_id: {resource_id} and category: {category}")
            response = self.table.delete_item(Key={"resource_id": resource_id, "category": category})
            print(f"Delete response: {response}")
            return True
        except Exception as e:
            print(f"Error deleting resource: {e}")
            traceback.print_exc()
            return False

    def store_resource(self, category, resource_link, description=""):
        """
        Store a resource under a given category, ensuring category consistency and no duplicate links.
        """
        category = category.strip().lower()  # Normalize category format
        resource_link = resource_link.strip()  # Normalize resource link
        description = description.strip().lower()  # Normalize description

        try:
            # Check for duplicate resource_link
            duplicate_response = self.table.scan(
                FilterExpression=Attr("resource_link").eq(resource_link)
            )
            if duplicate_response.get("Items", []):
                print(f"Duplicate resource_link found: {resource_link}. Skipping storage.")
                return False

            print(f"Attempting to store: {resource_link} in category {category}")
            
            # Generate a unique resource_id
            resource_id = str(uuid.uuid4())
            
            # Store item with the right structure including the required resource_id
            response = self.table.put_item(
                Item={
                    "resource_id": resource_id,  # Adding the required key
                    "category": category,
                    "resource_link": resource_link,
                    "description": description
                }   
            )
            
            print(f"DynamoDB Response: {response}")
            print(f"Successfully stored: {resource_link} in category {category}")
            return True  # Success flag
        except Exception as e:
            print(f"Error storing resource: {e}")
            traceback.print_exc()
            return False

    def get_resources_by_category(self, category):
        """
        Retrieve resources for a given category, handling case mismatches.
        """
        category = category.strip().lower()  # Normalize input category
        
        try:
            # Since we're not using category as the partition key, we need to use scan with a filter
            response = self.table.scan(
                FilterExpression=Attr("category").eq(category)
            )
            
            return response.get("Items", [])
        except Exception as e:
            print(f"Error getting resources: {e}")
            traceback.print_exc()
            return []

    def search_resources(self, keyword):
        """
        Search for resources containing the keyword in description (case-insensitive and partial match).
        """
        try:
            keyword = keyword.strip().lower()  # Normalize the keyword
            print(f"Searching for keyword: {keyword}")
            
            # Scan the table for items containing the keyword in description
            response = self.table.scan(
                FilterExpression=Attr("description").contains(keyword)
            )
            
            print(f"Search response: {response}")
            items = response.get("Items", [])
            print(f"Items found: {items}")
            return items
        except Exception as e:
            print(f"Error searching resources: {e}")
            traceback.print_exc()
            return []


# Test function to check table structure
def describe_table(table_name):
    try:
        dynamodb = boto3.client('dynamodb')
        response = dynamodb.describe_table(TableName=table_name)
        key_schema = response['Table']['KeySchema']
        print(f"Table key schema: {key_schema}")
        return key_schema
    except Exception as e:
        print(f"Error describing table: {e}")
        traceback.print_exc()
        return None

# Standalone test if running this file directly
if __name__ == "__main__":
    describe_table("CareerResources")