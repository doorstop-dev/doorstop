from doorstop.core import builder

tree = builder.build()
print("issues...")
for issue in tree.get_issues():
    print(issue)
# test
