import os
import django


# Step 1: Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'insb_port.settings')  # replace with your project name
django.setup()

from task_assignation.models import Task_Category

# Step 3: Do stuff
def do_shit():
    updated = 0
    errors = 0

    all_objects = Task_Category.objects.filter(enabled=True)
    for obj in all_objects:
        try:
            obj.points = obj.points * 5
            obj.save()
            updated += 1
        except Exception as e:
            print(f"[Error] Failed on ID {obj.id}: {e}")
            errors += 1

    print(f"\n✅ Done: {updated} objects.")
    if errors:
        print(f"❌ Errors: {errors}")

if __name__ == '__main__':
    do_shit()