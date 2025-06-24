import os

for root, dirs, files in os.walk("../../Dataset/rawframes", topdown=False):
    for name in files:
        if 'checkpoint' in name or 'Store' in name:
            continue

        oldNamePath = os.path.join(root, name)

        tempName1 = name.split('_')[1]  # e.g., "44_000054.jpg" -> "000054.jpg"
        tempName2 = tempName1.split('.')[0]  # "000054.jpg" -> "000054"
        tempName3 = str(int(tempName2)).zfill(5)  # "000054" -> "00054"
        newName = 'img_' + tempName3 + '.jpg'
        newNamePath = os.path.join(root, newName)

        if not os.path.exists(newNamePath):
            os.rename(oldNamePath, newNamePath)
        else:
            print(f"Skipped rename to avoid overwrite: {newNamePath}")
