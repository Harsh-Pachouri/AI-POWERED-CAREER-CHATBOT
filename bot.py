import json
import boto3
import telegram
import traceback
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from faiss_search import AIResourceSearch
from db_manager import DBManager

# Load environment variables

TOKEN = "insert token here"
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set. Please configure your environment.")

bot = telegram.Bot(token=TOKEN)

# AWS Setup
try:
    session = boto3.Session()
    credentials = session.get_credentials()
    if credentials is None:
        print("WARNING: No AWS credentials found!")
    else:
        print(f"AWS credentials found for user: {session.client('sts').get_caller_identity().get('Arn')}")
        
    dynamodb = boto3.resource('dynamodb')
    TABLE_NAME = "CareerResources"

    # Check if table exists
    table_exists = TABLE_NAME in [table.name for table in dynamodb.tables.all()]
    if not table_exists:
        print(f"WARNING: Table '{TABLE_NAME}' does not exist!")
    
    db_manager = DBManager(TABLE_NAME)
    search_engine = AIResourceSearch()
except Exception as e:
    print(f"Error during AWS setup: {str(e)}")
    traceback.print_exc()

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Welcome! Use the following commands:\n"
        "   • /store <link> <description> : Store a resource\n"
        "   • /search <keyword> : Search for resources\n"
        "   • /delete <link> : Delete the last searched resource\n"
        "   • /delete_all : Delete all resources\n"
    )

async def store_resource(update: Update, context: CallbackContext):
    """
    Store a resource using /store <link> <description>.
    """
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Usage: /store <link> <description>")
            return
        
        link, description = args[0], " ".join(args[1:])
        category = "general"

        success = db_manager.store_resource(category, link, description)
        if success:
            search_engine.add_to_index(link, description)
            await update.message.reply_text("Resource saved successfully!")
        else:
            await update.message.reply_text("Failed to save resource. Check server logs.")
    except Exception as e:
        print(f"Exception during store_resource: {e}")
        traceback.print_exc()
        await update.message.reply_text("An error occurred while storing the resource.")

async def search_resource(update: Update, context: CallbackContext):
    """
    Search for resources using /search <keyword>.
    Stores the best match for easy deletion.
    """
    try:
        args = context.args
        if not args:
            await update.message.reply_text("Usage: /search <keyword>")
            return
        
        query = " ".join(args)
        print(f"Searching for: {query}")

        # Semantic search using FAISS
        best_match_link = search_engine.search(query)
        
        if best_match_link:
            # Fetch details from DB
            matching_items = db_manager.search_resources_by_link(best_match_link)
            if matching_items:
                item = matching_items[0]
                resource_id = item["resource_id"]
                category = item["category"]

                # Store in user context for deletion
                context.user_data["last_search"] = {
                    "resource_id": resource_id,
                    "category": category,
                    "link": best_match_link
                }

                await update.message.reply_text(f"Best match: {best_match_link}\n\nUse /delete {best_match_link} to remove it.")
                return
        
        # Fallback to keyword search in DB
        db_results = db_manager.search_resources(query)
        if db_results:
            response = "Here are some matches:\n\n"
            for item in db_results[:3]:
                response += f"• {item['resource_link']} - {item['description']}\n\n"

                # Store the first result for easy deletion
                if "last_search" not in context.user_data:
                    context.user_data["last_search"] = {
                        "resource_id": item["resource_id"],
                        "category": item["category"],
                        "link": item["resource_link"]
                    }
                    
            await update.message.reply_text(response + "\nUse /delete <link> to remove a resource.")
        else:
            await update.message.reply_text("No matching resources found.")
    except Exception as e:
        print(f"Exception during search_resource: {e}")
        traceback.print_exc()
        await update.message.reply_text("An error occurred while searching.")

async def delete_resource(update: Update, context: CallbackContext):
    """
    Delete a resource using /delete <link>.
    Automatically fetches the resource ID and category from the last search.
    """
    try:
        args = context.args
        if not args:
            await update.message.reply_text("Usage: /delete <link>")
            return
        
        link_to_delete = args[0]

        # Check if the last searched item matches
        last_search = context.user_data.get("last_search")
        if not last_search or last_search["link"] != link_to_delete:
            await update.message.reply_text("No matching search result found for deletion.")
            return

        # Extract stored details
        resource_id = last_search["resource_id"]
        category = last_search["category"]

        # Perform deletion
        success = db_manager.delete_resource(resource_id, category)
        if success:
            await update.message.reply_text(f"Resource {link_to_delete} deleted successfully.")
        else:
            await update.message.reply_text(f"Failed to delete {link_to_delete}.")
    except Exception as e:
        print(f"Exception during delete_resource: {e}")
        traceback.print_exc()
        await update.message.reply_text("An error occurred while deleting the resource.")

async def delete_all_entries(update: Update, context: CallbackContext):
    """
    Delete all entries using /delete_all.
    """
    try:
        success = db_manager.delete_all_entries()
        if success:
            await update.message.reply_text("All entries deleted successfully.")
        else:
            await update.message.reply_text("Failed to delete all entries.")
    except Exception as e:
        print(f"Exception during delete_all_entries: {e}")
        traceback.print_exc()
        await update.message.reply_text("An error occurred while deleting all entries.")

async def end_conversation(update: Update, context: CallbackContext):
    await update.message.reply_text("Conversation ended. Type /start to begin again.")

def main():
    try:
        app = Application.builder().token(TOKEN).build()

        # Add command handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("store", store_resource))
        app.add_handler(CommandHandler("search", search_resource))
        app.add_handler(CommandHandler("delete", delete_resource))
        app.add_handler(CommandHandler("delete_all", delete_all_entries))

        print("Bot is running...")
        app.run_polling()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
