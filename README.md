# ale3andro's lab_organizr
## Περί
Το λογισμικό αυτό είναι ένα έργο που φιλοδοξεί να κάνει την ευκολότερη τη 
δουλειά ενός Administrator ενός σχολικού εργαστηρίου Πληροφορικής που 
τρέχει Linux. 
Μια σειρά από διαχειριστικές εργασίες (αποστολή αρχείων, λήψη αρχείων, 
κλείσιμο διεργασίας, επανεκκίνηση X Server κλπ) μπορούν να γίνουν με 2-3 κλικ
ώστε να μην χάνεται πολύτιμος χρόνος μέσα στην τάξη.
Επίσης γίνονται παράλληλα με χρήση πολλαπλών threads με αποτέλεσμα οι 
παραπάνω εργασίες να γίνονται πολύ πολύ ταχύτερα

## Τι έχει γίνει (features)
* Κατηγορίες clients (client classes) ανάλογα με την διανομή Linux που τρέχουν
* Δυνατότητα επιλογής σύνδεσης ως desktop user ή user με δικαιώματα sudo
* Χρήση πολλαπλών threads ώστε να τελειώνουν οι εργασίας πολύ γρηγορότερα
* Ενσωμάτωση εργασιών σε μορφή modules γραμμένα σε json, δυνατότητα δημιουργίας
περισσότερν Modules χωρίς αλλαγή κώδικα
* Υποστήριξη αποθήκευσης αρχείων (που λαμβάνονται από τους clients) σε online ή offline folder
* Δυνατότητα λήψης & αποστολής αρχείων στους clients με επιλογή τμήματος & ημερομηνίας
* Δυνατότητα εύκολης προσθήκης περισσότερων clients με προσθήκη των χαρακτηριστικών τους στο configuration file
* Δυνατότητα λήψης αρχείων (όλων ή με συγκεκριμένες επεκτάσεις) από τις Επιφάνειες εργασίας των clients και αποθήκευση σε online ή offline φάκελο, σε υποφάκελο τμήματος και ημερομηνίας λήψης

## Τι δεν έχει γίνει ( & πρέπει να γίνει)
* Μαζική επιστροφή αρχείων
* Επιλογή ημερομηνιών για επιστροφή αρχείων
* Όταν επιλέγονται περισσότερα τους ενός actions, δεν εκτελούνται με τη σωστή σειρά
* Τα κουμπιά πάνω & κάτω δεν για τη σειρά των επιλεγμένων actions δεν λειτουργούν
* Προσθήκη python-logging module


